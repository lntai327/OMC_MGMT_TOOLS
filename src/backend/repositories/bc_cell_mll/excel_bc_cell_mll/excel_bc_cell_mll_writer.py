import os
import re
import openpyxl
import shutil
from openpyxl.styles import Font #Border, Side, Alignment, PatternFill

from backend.constant import type as T
from backend.constant import excel_struct_info as ESI
from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.util.time_util import TimeUtil
from share.constant import constant as SC
from share.constant import type as ST

class ExcelBcCellMllWriter:
    def __init__(self):
        explorer_util = ExplorerUtil()
        output_folder_path = explorer_util.create_outfolder_by_rpdate()
        self.excel_output_path = os.path.join(
            output_folder_path,
            (
                f'{SC.K_EXCEL_BC_CELL_MLL_NAME}'
                f'_{
                    str(TimeUtil().get_detail_current_time_str())\
                    .replace('/', '')\
                    .replace(':', '')\
                    .replace(' ', '_') or ''
                }'
                f'.xlsx'
            )
        )
        excel_output_template_path = explorer_util.get_output_template_file_path(
            SC.K_EXCEL_BC_CELL_MLL_TEMPLATE)
        shutil.copy(excel_output_template_path, self.excel_output_path)

    def write_data_to_excel_all_header_list(self, data_list, sheet_name, gen_stt = True):
        wb = openpyxl.load_workbook(self.excel_output_path)
        ws = wb[sheet_name]
        if re.search("Chi tiết", sheet_name, re.IGNORECASE):
            sheet_info_name = 'Chi tiết TTVT X'
        else:
            sheet_info_name = sheet_name

        sheet_info = ESI.EXCEL_STRUCT_INFO[SC.K_EXCEL_BC_CELL_MLL_KEY]\
            [SC.K_SHEET_INFO][sheet_info_name]

        (start_row, start_col, start_header_list, start_req_header_list, \
                start_req_header_indices_list) = \
            ExcelHandleUtil().get_start_row_info(ws, sheet_info)

        counter = 0
        for item in data_list:
            if gen_stt:
                counter += 1
                item[SC.K_STT] = counter
            row_data = [item.get(header, SC.K_UI_MSG_MISS_DB) for header in start_header_list]
            ws.append(row_data)

        # --- set format ---
        for row in ws.iter_rows(min_row=start_row+1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER
                cell.font = T.EX_FORMAT_NORMAL_FONT

        wb.save(self.excel_output_path)
        wb.close()

    def write_data_to_excel_bc_ctiet_ttvt_x(self, data_dict: dict):
        for k, v in data_dict.items():
            if re.search("Trung tâm Viễn thông", k, re.IGNORECASE):
                sheet_name = f'Chi Tiết TTVT {k[21:].strip()}'
            else:
                sheet_name = f'Chi Tiết TTVT UNKNOWN'

            wb = openpyxl.load_workbook(self.excel_output_path)
            template_sheet = wb['Chi tiết TTVT X']
            ws = wb.copy_worksheet(template_sheet)
            ws.title = sheet_name
            ws.sheet_state = 'visible'
            ws.sheet_view.showGridLines = False
            wb.save(self.excel_output_path)
            wb.close()
            self.write_data_to_excel_all_header_list(v, sheet_name)

    def write_data_to_excel_bc_tong_hop_sheet(self, data_list, sheet_name):
        dynamic_info_util = DynamicInfoUtil()
        wb = openpyxl.load_workbook(self.excel_output_path)
        ws = wb[sheet_name]

        # Report title
        site: str = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        full_site_name = ""
        match site.lower():
            case ST.Site.DONG.value:
                full_site_name = "Site Đông"
            case ST.Site.TAY.value:
                full_site_name = "Site Tây"
            case ST.Site.ALL_SITE.value:
                full_site_name = "Tất Cả Site"

        ws.cell(row=1, column= 1).value \
            = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_TITLE) +\
            f' ({full_site_name})'
        ws.cell(row=1, column= 1).font = T.EX_FORMAT_TITLE_FONT

        ws.cell(row=2, column= 1).value \
            = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SRC_DATA)
        ws.cell(row=2, column= 1).font = T.EX_FORMAT_TITLE_FONT

        # Report date
        ws.cell(row=5, column= 4).value \
            = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_DATE)
        ws.cell(row=5, column= 4).font = T.EX_FORMAT_BOLD_FONT

        # RP time cpare
        need_compare = dynamic_info_util.get_value(
            2, SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, SC.K_SELECT
        )
        if need_compare == "1":
            time_cpare = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE)
            ws.cell(row=5, column= 8).value = time_cpare
            ws.cell(row=5, column= 8).font = T.EX_FORMAT_BOLD_FONT

        # data row
        start_row = 7
        for item in data_list:
            row_data = [item.get(header, "N/A") for header in range(1, 15)]
            ws.append(row_data)

        # --- set format ---
        for row in ws.iter_rows(min_row=start_row, max_row=ws.max_row,
                                   min_col=1, max_col=ws.max_column):
            for cell in row:
                #
                cell.border = T.EX_FORMAT_THIN_BORDER

                #
                if cell.column not in [1,2]:
                    cell.alignment = T.EX_FORMAT_ALIGNMENT_CENTER

            ttvt = row[1].value
            if ttvt and ("tổng cell" in str(ttvt).lower()) :
                for cell in row:
                    if cell.column not in [2,3]:
                        cell.font = Font(
                            bold=True, name="Times New Roman", color="FF0000"
                        )
                    else:
                        cell.font = Font(
                            bold=True, name="Times New Roman")

        wb.save(self.excel_output_path)
        wb.close()