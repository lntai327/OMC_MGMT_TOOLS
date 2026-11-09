import traceback
import time
import openpyxl

from backend.constant import excel_struct_info as ESI
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import constant as SC

class ExcelLoaderUtil:
    def __init__(self):
        pass

    def load_items(
            self,
            sheet_name: str,
            sheet_info_key: str,
            excel_info_key: str,
            wb: openpyxl.Workbook = None,
            excel_path: str = None,
            close_wb: bool = True
    ) -> list[dict]:
        items_list: list[dict] = []
        try:
            t_start = time.perf_counter()

            if wb is None:
                wb = openpyxl.load_workbook(excel_path, data_only=True) #read_only=True
            ws = wb[sheet_name]

            excel_struct_info: dict = ESI.EXCEL_STRUCT_INFO[excel_info_key]
            sheet_info_dic = excel_struct_info[SC.K_SHEET_INFO][sheet_info_key]
            start_cell = sheet_info_dic[SC.K_START_CELL]
            require_col = sheet_info_dic[SC.K_REQUIRE_COL]

            rows = ws.iter_rows(values_only=True) #max_col=search_max_col

            # find header row (first row containing start_cell)
            header_row = None
            header_idx = None
            for r_idx, row in enumerate(rows, start=1):
                if row is None:
                    continue
                # normalize row values to strings for robust matching
                if any(cell is not None and str(cell).strip() == str(start_cell).strip() for cell in row):
                    header_row = list(row)
                    header_idx = r_idx
                    break

            if header_row is None:
                LoggerUtil.get_logger().error('header not found via iter_rows')
                raise RuntimeError('header not found via iter_rows')

            # compute indices of required columns
            req_idx_list = self._get_req_colum_idx_list(header_row, require_col)

            # iterate remaining rows
            # create a fresh iterator to avoid dealing with a partially consumed one
            rows = ws.iter_rows(min_row=header_idx+1, values_only=True) #max_col=data_max_col
            timing_sample = []
            for r_idx, row in enumerate(rows, header_idx+1):
                # pick only required columns
                req_colums_value_list = \
                    [
                        str(row[idx]).strip() if idx < len(row) \
                        else None for idx in req_idx_list
                    ]
                req_row_dic = dict(zip(require_col, req_colums_value_list))
                # LoggerUtil.get_logger().debug(
                #     f'r_idx {r_idx} req_row_dic {req_row_dic}\n'
                # )
                items_list.append(req_row_dic)
                # capture some sample timings every N rows
                if (r_idx - header_idx) % 500 == 0:
                    timing_sample.append((r_idx, int((time.perf_counter() - t_start) * 1000)))

            t_end = time.perf_counter()

            # LoggerUtil.get_logger().debug(
            #     f'ExcelLoaderUtil.load_items: sheet={sheet_name} rows={len(items_list)} elapsed_ms={int((t_end - t_start) * 1000)} samples={timing_sample}'
            # )

            # Ensure the workbook is closed to release the file handle on Windows
            if close_wb and wb:
                try:
                    wb.close()
                except Exception:
                    LoggerUtil.get_logger().error(
                        f'ExcelLoaderUtil.load_items : unable to close workbook after successful read')
                    raise RuntimeError(
                        f'ExcelLoaderUtil.load_items : unable to close workbook after successful read')

            return items_list
        except Exception as e:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(
                f'ExcelLoaderUtil.load_items: failed for {sheet_name}, {e}, traceback: {tb}')
            raise RuntimeError(
                f'ExcelLoaderUtil.load_items: failed for {sheet_name}, {e}, traceback: {tb}')

    def get_start_row_info(self, ws, sheet_info_dic) -> tuple:
        max_row = ws.max_row
        max_col = ws.max_column

        start_req_header_list = sheet_info_dic[SC.K_REQUIRE_COL]

        for row_idx in range(1, max_row + 1):
            row_values_list = []
            for col_idx in range(1, max_col + 1):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                row_values_list.append(cell_value)
            # if row_idx < 5:
            #     output_str = f'get_start_row_info Row {row_idx} row_values_list: {row_values_list}\n'
            #     sys.stdout.buffer.write(output_str.encode('utf-8', errors='replace'))

            if sheet_info_dic[SC.K_START_CELL] in row_values_list:
                col_idx = row_values_list.index(sheet_info_dic[SC.K_START_CELL]) + 1
                break

        req_idx_list = self._get_req_colum_idx_list(
            row_values_list, sheet_info_dic[SC.K_REQUIRE_COL]
        )

        return row_idx, col_idx, row_values_list, start_req_header_list, req_idx_list

    def _get_req_colum_idx_list(self, header_list, req_cols_list):
        # build a normalized header -> idx map to tolerate minor formatting differences
        header_idx_map = {}
        for idx, h in enumerate(header_list):
            try:
                header_idx_map[str(h).strip()] = idx
            except Exception:
                header_idx_map[h] = idx

        req_idx_list = []
        for req_col in req_cols_list:
            key = str(req_col).strip()
            if key in header_idx_map:
                req_idx_list.append(header_idx_map[key])
            else:
                LoggerUtil.get_logger().error(
                    f'ExcelLoaderUtil._get_req_colum_idx_list req_col {req_col} not in header_idx_map')
                raise RuntimeError(
                    f'ExcelLoaderUtil._get_req_colum_idx_list req_col {req_col} not in header_idx_map')

        return req_idx_list

    def get_sheet_dynamic_name(self, file_info_key: str, file_path: str, sheet_key: str) -> str|None:
        required_sheet = DynamicInfoUtil().get_value(2, file_info_key, SC.K_REQUIRE_SHEET)
        try:
            wb = openpyxl.load_workbook(file_path)
        except Exception:
            LoggerUtil.get_logger().error(
                'ExcelLoaderUtil.get_sheet_dynamic_name : unable to open workbook')
            return None

        try:
            sheet_names = wb.sheetnames
            if not sheet_names:
                LoggerUtil.get_logger().error(
                    'ExcelLoaderUtil.get_sheet_dynamic_name : no sheet names found')
                return None

            for sheet_name in sheet_names:
                if sheet_name.startswith(required_sheet[sheet_key][SC.K_KEY]):
                    return sheet_name

            LoggerUtil.get_logger().error(
                'ExcelLoaderUtil.get_sheet_dynamic_name : required sheet not found')
            return None
        finally:
            try:
                wb.close()
            except Exception:
                LoggerUtil.get_logger().error(
                    f'ExcelLoaderUtil.get_sheet_dynamic_name : unable to close workbook {file_path}')
