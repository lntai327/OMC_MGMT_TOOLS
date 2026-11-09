import os
import shutil
import traceback
from datetime import datetime
from typing import Generator, List, Dict, Any, Optional
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from app.constant import excel_struct_info as ESI
from app.constant import constant as SC
from app.constant import type as T
from app.core.logging import get_logger

logger = get_logger("excel_streamer")

class ExcelStreamer:
    """Streaming Excel reader and writer for memory-efficient handling of large datasets."""

    @staticmethod
    def convert_old_xls_to_xlsx(file_path: str) -> str:
        """
        Tự động chuyển đổi ngầm định dạng cũ .xls sang .xlsx (sử dụng xlrd + openpyxl).
        Nếu file đã là .xlsx thì trả về nguyên vẹn đường dẫn.
        """
        if not file_path.lower().endswith(".xls"):
            return file_path

        import xlrd

        base_name, _ = os.path.splitext(file_path)
        new_file_path = f"{base_name}_converted.xlsx"

        logger.info(f"Converting legacy Excel .xls: '{file_path}' -> '{new_file_path}'")
        try:
            xls_wb = xlrd.open_workbook(file_path, formatting_info=False)
            xlsx_wb = openpyxl.Workbook()
            xlsx_wb.remove(xlsx_wb.active)  # Xóa sheet mặc định

            for sheet_idx in range(xls_wb.nsheets):
                xls_ws = xls_wb.sheet_by_index(sheet_idx)
                xlsx_ws = xlsx_wb.create_sheet(title=xls_ws.name)

                for r in range(xls_ws.nrows):
                    row_vals = []
                    for c in range(xls_ws.ncols):
                        cell = xls_ws.cell(r, c)
                        if cell.ctype == xlrd.XL_CELL_DATE:
                            try:
                                val = xlrd.xldate_as_datetime(cell.value, xls_wb.datemode)
                                row_vals.append(val.strftime("%Y-%m-%d %H:%M:%S"))
                            except Exception:
                                row_vals.append(cell.value)
                        elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                            row_vals.append(bool(cell.value))
                        elif cell.ctype in (xlrd.XL_CELL_ERROR, xlrd.XL_CELL_EMPTY):
                            row_vals.append(None)
                        else:
                            row_vals.append(cell.value)
                    xlsx_ws.append(row_vals)

            xlsx_wb.save(new_file_path)
            xlsx_wb.close()
            logger.info(f"Conversion successful -> '{new_file_path}'")
            return new_file_path
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"convert_old_xls_to_xlsx failed for '{file_path}': {e}\n{tb}")
            raise RuntimeError(f"Không thể chuyển đổi file .xls sang .xlsx: {e}")

    @staticmethod
    def _find_header_idx_mapping(
        ws: Worksheet,
        start_cell_val: str,
        require_col_list: List[str],
        header_row_range: int = 1,
    ) -> tuple[Dict[str, int], int]:
        target_start_cell_val = str(start_cell_val).strip().lower() if start_cell_val else ""
        start_row_idx: Optional[int] = None

        rows_header = list(
            ws.iter_rows(max_row=header_row_range, values_only=True)
        )

        #
        if target_start_cell_val:
            for r_idx, row in enumerate(rows_header, start=1):
                if row is None:
                    continue
                if any(cell is not None and str(cell).strip().lower() == target_start_cell_val for cell in row):
                    start_row_idx = r_idx
                    break

        if start_row_idx is None:
            err_msg = (
                f"Không tìm thấy dòng tiêu đề trong {header_row_range} dòng đầu "
                f"(tìm theo '{start_cell_val}' hoặc các cột bắt buộc)."
            )
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        #
        require_col_set = {str(col).strip().lower() for col in require_col_list}
        header_idx_map: Dict[str, int] = {}
        last_header_row_idx = start_row_idx

        for r_idx, row in enumerate(rows_header[start_row_idx - 1:], start=start_row_idx):
            if row is None:
                continue
            has_matching_header = False
            for c_idx, cell in enumerate(row):
                if cell is not None:
                    norm_key = str(cell).strip().lower()
                    if norm_key and norm_key in require_col_set:
                        if norm_key not in header_idx_map:
                            header_idx_map[norm_key] = c_idx
                            has_matching_header = True
            if has_matching_header:
                last_header_row_idx = r_idx

        #
        req_header_idx_dict: Dict[str, int] = {}
        missing_cols: List[str] = []

        for req_col in require_col_list:
            norm_req = str(req_col).strip().lower()
            if norm_req in header_idx_map:
                req_header_idx_dict[req_col] = header_idx_map[norm_req]
            else:
                missing_cols.append(req_col)

        if missing_cols:
            err_msg = f"File Excel thiếu các cột bắt buộc: {missing_cols}"
            logger.error(f"{err_msg}. Các cột tìm thấy trong file: {list(header_idx_map.keys())}")
            raise RuntimeError(err_msg)

        data_start_row_idx = last_header_row_idx + 1
        return req_header_idx_dict, data_start_row_idx

    @classmethod
    def read_rows_chunked(
        cls,
        file_path: str,
        file_key: str,
        chunk_size: int = 500,
        header_row_range: int = 1,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        #
        actual_file_path = cls.convert_old_xls_to_xlsx(file_path)

        if file_key not in ESI.EXCEL_STRUCT_INFO:
            raise ValueError(f"file_key '{file_key}' không tồn tại trong EXCEL_STRUCT_INFO")

        struct_info = ESI.EXCEL_STRUCT_INFO[file_key]
        sheet_data_cfg = struct_info.get(SC.K_SHEET_INFO, {}).get(SC.K_SHEET_DATA, {})

        sheet_key_pattern = str(sheet_data_cfg.get(SC.K_KEY, "")).strip().lower()
        start_cell_val = sheet_data_cfg.get(SC.K_START_CELL, "")
        require_col_dict: dict = sheet_data_cfg.get(SC.K_REQUIRE_COL_MAP, {})
        # Map chuẩn hóa chữ thường -> tên trường DB
        norm_require_col_map = {
            str(k).strip().lower(): v for k, v in require_col_dict.items()
        }

        wb = openpyxl.load_workbook(actual_file_path, read_only=True, data_only=True)

        try:
            #
            matched_sheets = [
                name for name in wb.sheetnames
                if sheet_key_pattern in name.lower()
            ]

            if not matched_sheets:
                err_msg = f"Can not find any sheet with key '{sheet_key_pattern}' in '{actual_file_path}'"
                logger.error(err_msg)
                raise RuntimeError(err_msg)

            logger.info(
                f"Found {len(matched_sheets)} sheet with key '{sheet_key_pattern}': {matched_sheets}"
            )

            # 3. Stream đọc từng dòng qua TẤT CẢ các sheet khớp cấu trúc
            chunk: List[Dict[str, Any]] = []

            for sheet_name in matched_sheets:
                ws = wb[sheet_name]
                logger.info(f"Đang đọc dữ liệu từ sheet: '{sheet_name}'")

                # Tìm dòng header và index các cột require_col_map cho sheet này
                req_col_idx_map, data_start_row_idx = cls._find_header_idx_mapping(
                    ws=ws,
                    start_cell_val=start_cell_val,
                    require_col_list=list(require_col_dict.keys()),
                    header_row_range=header_row_range,
                )

                logger.info(f"Sheet '{sheet_name}': start read data from line {data_start_row_idx}")

                rows_iter = ws.iter_rows(
                    min_row=data_start_row_idx, values_only=True
                )

                for row in rows_iter:
                    if not row or all(c is None for c in row):
                        continue  # Bỏ qua dòng trống hoàn toàn

                    row_dict: Dict[str, Any] = {}
                    for req_col, col_idx in req_col_idx_map.items():
                        val = row[col_idx] if col_idx < len(row) else None
                        if val is not None:
                            val = str(val).strip()
                        else:
                            val = ""

                        #
                        norm_req = req_col.strip().lower()
                        field_name = norm_require_col_map.get(norm_req, require_col_dict.get(req_col, norm_req))
                        row_dict[field_name] = val

                    chunk.append(row_dict)

                    if len(chunk) >= chunk_size:
                        logger.info(
                            f"read {len(chunk)} row"
                        )
                        yield chunk
                        chunk = []

            #
            if chunk:
                f"read last {len(chunk)} row"
                yield chunk

        finally:
            wb.close()
            # Dọn dẹp file tạm nếu trước đó là file .xls được convert
            if actual_file_path != file_path and os.path.exists(actual_file_path):
                try:
                    os.remove(actual_file_path)
                except Exception:
                    pass

    @staticmethod
    def export_megawan(
        template_path: str,
        output_path: str,
        records: List[Dict[str, Any]]
    ) -> str:
        MEGAWAN_EXPORT_HEADERS = [
            SC.K_ACTION,
            SC.K_MA_TB,
            SC.K_MA_LT_MA_TB_SUB,
            SC.K_TEN_TH_BAO,
            SC.K_DIA_CHI,
            SC.K_ID,
            SC.K_DIEM_CUOI,
            SC.K_IP_SRC,
            SC.K_IP_DES,
            SC.K_SVLAN_CVLAN,
            SC.K_CAP_ADSL,
            SC.K_CAP_ODF,
            SC.K_LAST_UPDATE,
            SC.K_GHI_CHU,
            SC.K_IP,
            SC.K_TEN_HE_THONG,
            SC.K_PORT_SWITCH,
            SC.K_UPE,
            SC.K_LOAI_HINH_TB,
            SC.K_TRANG_THAI,
            SC.K_TOC_DO,
            SC.K_DVI,
            SC.K_LOAI_KENH,
        ]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if os.path.exists(template_path):
            shutil.copy2(template_path, output_path)
            wb = openpyxl.load_workbook(output_path)
            ws = wb["data"]

        for row_idx, item in enumerate(records, start=2):
            for col_idx, key in enumerate(MEGAWAN_EXPORT_HEADERS, start=1):
                value = item.get(key, "") if key != SC.K_ACTION else ""
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

        wb.save(output_path)
        wb.close()
        return output_path
