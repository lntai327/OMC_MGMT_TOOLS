from share.util.logger_util import LoggerUtil
import os
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
import shutil


from backend.constant import type as T
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil
from share.constant import constant as SC

class ExcelDsachLoiWriter:
    def __init__(self):
        pass

    def _create_output(self):
        dynamic_info_util = DynamicInfoUtil()
        explorer_util = ExplorerUtil()

        self._output_folder_path = dynamic_info_util.get_value(
            2, SC.K_SCREEN_INPUT, SC.K_OUTPUT_PATH)
        #
        excel_dsach_loi_name = \
            SC.K_EXCEL_DSACH_LOI_TEMPLATE.replace("template.xlsx", "") + \
                dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_REPORT_TYPE) + \
                ".xlsx"

        excel_dsach_loi_path = os.path.join(
            self._output_folder_path, excel_dsach_loi_name
        )

        self.excel_output_template_path = \
            explorer_util.get_output_template_file_path(SC.K_EXCEL_DSACH_LOI_TEMPLATE)

        shutil.copy(
            self.excel_output_template_path, excel_dsach_loi_path
        )

        return excel_dsach_loi_path

    def _write_data_to_excel_by_header(self, sheet_opened: Worksheet, row_index, header_dict, data_dict):
        for header in header_dict.keys():
            sheet_opened.cell(row=row_index, column=header_dict[header]).value = data_dict[header]
            T.format_normal_cell(sheet_opened.cell(row=row_index, column=header_dict[header]))

    def write_excel(self, data: list):
        excel_path = self._create_output()

        wb = openpyxl.load_workbook(excel_path)
        sheet = wb[SC.K_SHEET_DSACH_LOI]
        header_dict = {
            SC.K_UI_ERROR: 2,
            SC.K_UI_DESCRIPTION: 3
        }
        start_row = 2
        for item in data:
            start_row += 1
            self._write_data_to_excel_by_header(sheet, start_row, header_dict, item)

        wb.save(excel_path)
        wb.close()

        return excel_path