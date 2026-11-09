from openpyxl.utils import get_column_letter
from copy import copy
import traceback
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from PIL import ImageFont
from pathlib import Path

from backend.constant import excel_struct_info as ESI
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import constant as SC

class ExcelHandleUtil:
    def __init__(self):
        pass

    def load_items(
            self,
            sheet_name: str,
            sheet_info_key: str,
            excel_info_key: str,
            wb: openpyxl.Workbook = None,
            excel_path: str = None,
            header_row_range: int = 1
    ) -> list[dict]:
        items_list: list[dict] = []
        wb_opened_locally = False
        try:
            if wb is None:
                wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
                wb_opened_locally = True
            ws: Worksheet = wb[sheet_name]
            ws._max_row = None
            ws._max_column = None

            excel_struct_info: dict = ESI.EXCEL_STRUCT_INFO[excel_info_key]
            sheet_info_dic = excel_struct_info[SC.K_SHEET_INFO][sheet_info_key]
            start_cell_val = sheet_info_dic[SC.K_START_CELL]
            req_header_val = sheet_info_dic[SC.K_REQUIRE_COL]

            # compute indices of required columns
            req_header_col_idx_list: list = []
            header_endrow_idx: int = None
            if header_row_range == 1:
                req_header_col_idx_list, header_row_val_list, header_endrow_idx = self._get_req_colum_info(
                    ws,
                    start_cell_val,
                    req_header_val
                )
            else:
                req_header_col_idx_list, header_endrow_idx = self._get_req_colum_info_v1(
                    ws,
                    start_cell_val,
                    header_row_range,
                    req_header_val
                )

            if len(req_header_col_idx_list) == 0:
                LoggerUtil.get_logger().error(f'{self.__class__.__name__} header not found via iter_rows')
                raise RuntimeError('req_header_col_idx_list not found via iter_rows')

            # iterate remaining rows
            rows = ws.iter_rows(min_row=header_endrow_idx+1, values_only=True)
            for r_idx, row in enumerate(rows, header_endrow_idx+1):
                # pick only required columns
                req_colums_value_list: list[str] = []
                for idx in req_header_col_idx_list:
                    val = ''
                    if idx < len(row):
                        val = str(row[idx]).strip() if row[idx] != None else ''
                    else:
                        val = 'N/A'
                    req_colums_value_list.append(val)
                req_row_dic = dict(zip(req_header_val, req_colums_value_list))
                items_list.append(req_row_dic)

            LoggerUtil.get_logger().info(
                f"{self.__class__.__name__}  {excel_info_key} loaded {len(items_list)}"
            )

            return items_list
        except Exception as e:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(
                f'{self.__class__.__name__} load_items: failed for excel_info_key: {excel_info_key} excel_path: {excel_path} sheet_name: {sheet_name}, e: {e}, traceback: {tb}'
            )
            raise RuntimeError(
                f'{self.__class__.__name__} load_items: failed for {sheet_name}, {e}, traceback: {tb}'
            )
        finally:
            # Ensure the workbook is closed to release the file handle on Windows
            if wb_opened_locally and wb:
                try:
                    wb.close()
                except Exception:
                    LoggerUtil.get_logger().error(
                        f'{self.__class__.__name__} load_items : unable to close workbook after read'
                    )

    # client use only
    def get_start_row_info(self, ws, sheet_info_dic) -> tuple:
        req_header_list = sheet_info_dic[SC.K_REQUIRE_COL]

        req_header_col_idx_list, header_row_val_list, header_endrow_idx = self._get_req_colum_info(
            ws,
            sheet_info_dic[SC.K_START_CELL],
            req_header_list
        )

        col_start_idx = header_row_val_list.index(sheet_info_dic[SC.K_START_CELL]) + 1

        return header_endrow_idx, col_start_idx, header_row_val_list, req_header_list, req_header_col_idx_list

    def _get_req_colum_info(self,
                            ws,
                            start_cell_val: str,
                            req_cols_list: list
            ) -> tuple[list, list, int]:
        req_header_col_idx_list = []
        header_row_val_list = None
        header_endrow_idx: int = None

        rows = ws.iter_rows(values_only=True)

        for r_idx, row in enumerate(rows, start=1):
            if row is None:
                continue
            # normalize row values to strings for robust matching
            if any(cell is not None and str(cell).strip() == str(start_cell_val).strip() for cell in row):
                header_row_val_list = list(row)
                header_endrow_idx = r_idx
                break

        if not header_row_val_list:
            LoggerUtil.get_logger().error('header not found via iter_rows')
            raise RuntimeError('header not found via iter_rows')

        header_idx_map = {}
        for idx, h in enumerate(header_row_val_list):
            try:
                header_idx_map[str(h).strip()] = idx
            except Exception:
                header_idx_map[h] = idx

        for req_col in req_cols_list:
            key = str(req_col).strip()
            if key in header_idx_map:
                req_header_col_idx_list.append(header_idx_map[key])
            else:
                LoggerUtil.get_logger().error(
                    f'{self.__class__.__name__} _get_req_colum_info req_col {req_col} not in header_idx_map')
                raise RuntimeError(
                    f'{self.__class__.__name__} _get_req_colum_info req_col {req_col} not in header_idx_map')

        return req_header_col_idx_list, header_row_val_list, header_endrow_idx

    def _get_req_colum_info_v1(
            self,
            ws: Worksheet,
            start_cell_val: str,
            header_row_range: int,
            req_cols_list: list
    ) -> tuple[list, int]:
        req_header_col_idx_list = []
        start_r_idx: int = None

        target_start = str(start_cell_val).strip()

        # Find starting row index where start_cell_val is located
        for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row is None:
                continue
            if any(cell is not None and str(cell).strip() == target_start for cell in row):
                start_r_idx = r_idx
                break

        if start_r_idx is None:
            LoggerUtil.get_logger().error(
                f'{self.__class__.__name__} _get_req_colum_info_v1 : start cell "{start_cell_val}" not found via iter_rows'
            )
            raise RuntimeError(
                f'{self.__class__.__name__} _get_req_colum_info_v1 : start cell not found'
            )

        header_endrow_idx = header_row_range

        # Collect cell values across header_row_range starting from start_r_idx
        header_idx_map = {}
        for row in ws.iter_rows(min_row=start_r_idx, max_row=header_row_range, values_only=True):
            if row is None:
                continue
            for idx, cell in enumerate(row):
                if cell is not None:
                    key = str(cell).strip()
                    if key and key not in header_idx_map:
                        header_idx_map[key] = idx

        # Find column index for each required header
        for req_col in req_cols_list:
            key: str = str(req_col).strip()
            if key in header_idx_map:
                req_header_col_idx_list.append(header_idx_map[key])
            else:
                LoggerUtil.get_logger().error(
                    f'{self.__class__.__name__} _get_req_colum_info_v1 : req_col "{req_col}" not found in header range ({start_r_idx}..{header_endrow_idx})'
                )
                raise RuntimeError(
                    f'{self.__class__.__name__} _get_req_colum_info_v1 : req_col not found'
                )

        return req_header_col_idx_list, header_endrow_idx

    def get_sheet_dynamic_name(self, file_info_key: str, file_path: str, sheet_key: str) -> list[str]:
        """Return all sheet names whose name contains the sheet_name_key (case-insensitive)."""
        required_sheet = DynamicInfoUtil()\
            .get_value(2, file_info_key, SC.K_REQUIRE_SHEET)
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'{self.__class__.__name__} get_sheet_dynamic_name {file_info_key} : unable to open workbook : {file_path} : {e}')
            raise RuntimeError(
                f'{self.__class__.__name__} get_sheet_dynamic_name : unable to open workbook')

        try:
            sheet_names = wb.sheetnames
            if not sheet_names:
                LoggerUtil.get_logger().error(
                    f'{self.__class__.__name__} get_sheet_dynamic_name : no sheet names found')
                return []

            sheet_name_key = str(required_sheet[sheet_key][SC.K_KEY]).strip().lower()
            matched_sheets = [
                sn for sn in sheet_names
                if sheet_name_key in sn.lower()
            ]

            if not matched_sheets:
                LoggerUtil.get_logger().error(
                    f'{self.__class__.__name__} get_sheet_dynamic_name {file_info_key} : required sheet not found'
                )
                raise RuntimeError(
                    f'{self.__class__.__name__} get_sheet_dynamic_name {file_info_key} : required sheet not found'
                )

            LoggerUtil.get_logger().info(
                f'{self.__class__.__name__} get_sheet_dynamic_name {file_info_key} : found {len(matched_sheets)} sheet(s): {matched_sheets}'
            )

            return matched_sheets
        finally:
            try:
                wb.close()
            except Exception:
                LoggerUtil.get_logger().error(
                    f'{self.__class__.__name__} get_sheet_dynamic_name : unable to close workbook {file_path}')

    def convert_old_xls_to_xlsx(self, file_path: str) -> str:
        """
        Safely convert an old-format .xls file to .xlsx.

        The converted file is placed in the same directory as the source with
        the same file-stem and a .xlsx extension.

        Returns:
            str: Absolute path of the newly created .xlsx file.

        Raises:
            RuntimeError: If the conversion fails for any reason.
        """
        import os
        import xlrd
        from datetime import datetime

        try:
            # Build output path: same dir + same stem + .xlsx
            base, _ = os.path.splitext(file_path)
            new_file_path = base + ".xlsx"

            LoggerUtil.get_logger().info(
                f'{self.__class__.__name__} convert_old_xls_to_xlsx : converting "{file_path}" -> "{new_file_path}"'
            )

            # Open the source .xls workbook (formatting_info=False is faster/safer)
            xls_wb = xlrd.open_workbook(file_path, formatting_info=False)

            # Create the target .xlsx workbook
            xlsx_wb = openpyxl.Workbook()
            xlsx_wb.remove(xlsx_wb.active)  # remove default blank sheet

            for sheet_idx in range(xls_wb.nsheets):
                xls_ws = xls_wb.sheet_by_index(sheet_idx)
                xlsx_ws = xlsx_wb.create_sheet(title=xls_ws.name)

                for row_idx in range(xls_ws.nrows):
                    for col_idx in range(xls_ws.ncols):
                        cell = xls_ws.cell(row_idx, col_idx)

                        # Convert xlrd cell types to Python-native values
                        if cell.ctype == xlrd.XL_CELL_DATE:
                            try:
                                value = xlrd.xldate_as_datetime(
                                    cell.value, xls_wb.datemode
                                )
                            except Exception:
                                value = cell.value  # fallback to raw float
                        elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                            value = bool(cell.value)
                        elif cell.ctype == xlrd.XL_CELL_ERROR:
                            value = None  # skip error cells
                        elif cell.ctype == xlrd.XL_CELL_EMPTY:
                            value = None
                        else:
                            value = cell.value

                        xlsx_ws.cell(row=row_idx + 1, column=col_idx + 1, value=value)

            xlsx_wb.save(new_file_path)
            xlsx_wb.close()

            LoggerUtil.get_logger().info(
                f'{self.__class__.__name__} convert_old_xls_to_xlsx : conversion successful -> "{new_file_path}"'
            )

            return new_file_path

        except Exception as e:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(
                f'{self.__class__.__name__} convert_old_xls_to_xlsx : failed for "{file_path}" : {e}\n{tb}'
            )
            raise RuntimeError(
                f'{self.__class__.__name__} convert_old_xls_to_xlsx : failed for "{file_path}" : {e}'
            )

    def copy_cell_style(self, source_cell, target_cell):
        """Copy cell style (font, fill, alignment, border) from source to target"""
        if source_cell.has_style:
            target_cell.font = copy(source_cell.font)
            target_cell.fill = copy(source_cell.fill)
            target_cell.alignment = copy(source_cell.alignment)
            target_cell.border = copy(source_cell.border)
            target_cell.number_format = copy(source_cell.number_format)

    def copy_rows_with_formatting(self, ws, from_row, to_row, from_col, to_col, target_row, target_col):
        """
        Copy rows with values, formatting, and merged cells

        Args:
            ws: Worksheet object
            from_row: Starting row (1-indexed)
            to_row: Ending row (1-indexed, inclusive)
            from_col: Starting column (1-indexed)
            to_col: Ending column (1-indexed, inclusive)
            target_row: Target starting row (1-indexed)
            target_col: Target starting column (1-indexed)
        """
        # Calculate dimensions
        num_rows = to_row - from_row + 1
        num_cols = to_col - from_col + 1
        
        # 1. Copy cell values and styles
        for row_offset in range(num_rows):
            for col_offset in range(num_cols):
                source_cell = ws.cell(from_row + row_offset, from_col + col_offset)
                target_cell = ws.cell(target_row + row_offset, target_col + col_offset)
                
                # Copy value
                target_cell.value = source_cell.value
                # Copy style
                self.copy_cell_style(source_cell, target_cell)
        
        # 2. Copy merged cells
        merged_ranges_to_add = []
        for merged_range in ws.merged_cells.ranges:
            # Check if merged range overlaps with source area
            if (from_row <= merged_range.min_row <= to_row or 
                from_row <= merged_range.max_row <= to_row or
                (merged_range.min_row < from_row and merged_range.max_row > to_row)):
                
                # Calculate if merged range is within our copy area
                if (merged_range.min_col <= to_col and merged_range.max_col >= from_col and
                    merged_range.min_row <= to_row and merged_range.max_row >= from_row):
                    
                    # Calculate offset for merged range
                    min_row_offset = max(0, merged_range.min_row - from_row)
                    max_row_offset = min(num_rows - 1, merged_range.max_row - from_row)
                    min_col_offset = max(0, merged_range.min_col - from_col)
                    max_col_offset = min(num_cols - 1, merged_range.max_col - from_col)
                    
                    # Create new merged range at target location
                    new_min_row = target_row + min_row_offset
                    new_max_row = target_row + max_row_offset
                    new_min_col = target_col + min_col_offset
                    new_max_col = target_col + max_col_offset
                    
                    merged_ranges_to_add.append(f"{get_column_letter(new_min_col)}{new_min_row}:{get_column_letter(new_max_col)}{new_max_row}")
        
        # Add merged ranges
        for merged_range in merged_ranges_to_add:
            ws.merge_cells(merged_range)

    def remove_row(self, ws, start_row, end_row):
        rows_to_delete = end_row - start_row + 1
        if rows_to_delete > 0:
            ws.delete_rows(idx=start_row, amount=rows_to_delete)

    def remove_column(self, ws, start_col, end_col):
        cols_to_delete = end_col - start_col + 1
        if cols_to_delete > 0:
            ws.delete_cols(idx=start_col, amount=cols_to_delete)

    _PIL_FONT_CACHE = {}

    @classmethod
    def _get_pil_font(
        cls,
        size: 11,
        bold: bool = False,
        italic: bool = False,
    ):
        key = (
            size,
            bool(bold),
            bool(italic),
        )

        cached_font = cls._PIL_FONT_CACHE.get(key)

        if cached_font is not None:
            return cached_font

        if bold and italic:
            filename = "DejaVuSans-BoldOblique.ttf"

        elif bold:
            filename = "DejaVuSans-Bold.ttf"

        elif italic:
            filename = "DejaVuSans-Oblique.ttf"

        else:
            filename = "DejaVuSans.ttf"

        font_path = Path(
            ExplorerUtil().get_font_file_path(filename)
        )

        if not font_path.is_file():
            LoggerUtil.get_logger().error(
                f"Font file not found: {font_path}"
            )
            raise FileNotFoundError(
                f"Font file not found"
            )

        pil_font = ImageFont.truetype(
            str(font_path),
            size=size,
        )

        cls._PIL_FONT_CACHE[key] = pil_font

        return pil_font

    @classmethod
    def auto_fit_columns(
        cls,
        ws,
        col_idx_list: list[int],
        start_row: int,
        end_row: int,
        min_width: float = 10,
        max_width: float = 150,
        padding: int = 12,
    ):
        if not col_idx_list:
            return

        if start_row > end_row:
            return

        for column in col_idx_list:

            max_pixel_width = 0

            for row in range(
                start_row,
                end_row + 1,
            ):
                cell = ws.cell(
                    row=row,
                    column=column,
                )

                if cell.value is None:
                    continue

                # Convert Excel value to string
                value = str(cell.value)

                # ------------------------------------------------------
                # Get cell font information
                # ------------------------------------------------------

                excel_font = cell.font

                font_size = int(
                    round(
                        excel_font.sz or 11
                    )
                )

                is_bold = bool(
                    excel_font.bold
                )

                is_italic = bool(
                    excel_font.italic
                )

                pil_font = cls._get_pil_font(
                    size=font_size,
                    bold=is_bold,
                    italic=is_italic,
                )

                lines = (
                    value.splitlines()
                    or [""]
                )

                for line in lines:
                    # PIL bbox:
                    #
                    # (left, top, right, bottom)
                    #
                    bbox = pil_font.getbbox(line)

                    pixel_width = (
                        bbox[2] - bbox[0]
                    )

                    if pixel_width > max_pixel_width:
                        max_pixel_width = (
                            pixel_width
                        )

            # ----------------------------------------------------------
            # Empty column
            # ----------------------------------------------------------

            if max_pixel_width <= 0:
                continue

            # ----------------------------------------------------------
            # Convert pixel width to Excel column width.
            #
            # This is an approximation of Excel's column-width unit.
            # ----------------------------------------------------------

            excel_width = (
                max_pixel_width + padding
            ) / 7

            # ----------------------------------------------------------
            # Apply min/max
            # ----------------------------------------------------------

            excel_width = max(
                min_width,
                # min(
                #     excel_width,
                #     max_width,
                # ),
                excel_width,
            )

            # ----------------------------------------------------------
            # Set Excel column width
            # ----------------------------------------------------------

            column_letter = get_column_letter(
                column
            )

            ws.column_dimensions[
                column_letter
            ].width = excel_width