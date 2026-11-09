import os
import openpyxl
import shutil
from datetime import datetime, timedelta, timezone #date,
from openpyxl.styles import Font

from backend.constant import type as T
from backend.constant import excel_struct_info as ESI
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil

from share.constant import constant as SC
from share.constant import type as ST

class DataBcTgHop:
    def __init__(self, cbao_clr_item_list: list, cbao_nclr_item_list: list):
        self.cbao_clr_item_list = cbao_clr_item_list
        self.cbao_nclr_item_list = cbao_nclr_item_list

class ExcelBcMpdWriter:
    def __init__(self):
        dynamic_info_util = DynamicInfoUtil()
        explorer_util = ExplorerUtil()

        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._tht_ttvt_maker.load()

        self._output_folder_path = explorer_util.create_outfolder_fromtotime()

        rp_time_type = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE)
        rp_time = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME)
        site: str = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        if site.lower() == ST.Site.ALL_SITE.value:
            site = "2Site"

        cr_time = datetime.now(timezone(timedelta(hours=7))).strftime("%H%M%S")

        match rp_time_type:
            case ST.TimeType.WEEK.value:
                rp_time_type = "Tuan"
            case ST.TimeType.MONTH.value:
                rp_time_type = "Thang"
        self._excel_bc_chay_mpd_qua_bgs_name = \
            SC.K_EXCEL_BC_CHAY_MPD_NAME + \
            "_" + rp_time_type + rp_time + \
            "_" + site + \
            "_" + \
            cr_time + \
            ".xlsx"

        self._excel_output_path = os.path.join(
            self._output_folder_path,
            self._excel_bc_chay_mpd_qua_bgs_name
        )
        self._excel_output_template_path = \
            explorer_util.get_output_template_file_path(SC.K_EXCEL_BC_CHAY_MPD_QUA_BGS_TEMPLATE)
        shutil.copy(self._excel_output_template_path, self._excel_output_path)

        dynamic_info_util.set_value(
            self._output_folder_path, 2, SC.K_SCREEN_INPUT, SC.K_OUTPUT_PATH)

    def write_excel(
            self,
            data_bc_chi_tiet: list,
            data_bc_chi_tiet_nclr: list,
            data_bc_tghop: list
    ) -> str|None:
        self._write_data_to_excel_all_header_list(
            data_bc_chi_tiet, SC.K_SHEET_BC_CHI_TIET
        )

        self._write_data_to_excel_all_header_list(
            data_bc_chi_tiet_nclr, SC.K_SHEET_CANH_BAO_NCLR
        )

        self._write_data_to_excel_bc_tong_hop_sheet(
            data_bc_tghop, SC.K_SHEET_BAO_CAO_TONG_HOP
        )

        return self._excel_output_path

    def _write_data_to_excel_all_header_list(self, data_list, sheet_name):
        ttvt_unique_list = []
        #
        wb = openpyxl.load_workbook(self._excel_output_path)
        ws = wb[sheet_name]
        sheet_info = ESI.EXCEL_STRUCT_INFO[SC.K_EXCEL_BC_CHAY_MPD_QUA_BGS_KEY][SC.K_SHEET_INFO][sheet_name]
        (start_row, start_col, start_header_list, start_req_header_list, \
                start_req_header_indices_list) = \
            ExcelHandleUtil().get_start_row_info(ws, sheet_info)

        counter = 0
        for item in data_list:
            counter += 1
            ws = wb[sheet_name]
            item[SC.K_STT] = counter
            row_data = [item.get(header, SC.K_UI_MSG_MISS_DB) for header in start_header_list]
            ws.append(row_data)

            #
            if item[SC.K_TTVT_2] not in ttvt_unique_list:
                ttvt_unique_list.append(item[SC.K_TTVT_2])

        # --- set format ---
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER
                cell.font = T.EX_FORMAT_NORMAL_FONT

        req_row_dic = dict(zip(start_req_header_list, start_req_header_indices_list))
        for i in range(len(ttvt_unique_list)):
            ttvt: str = ttvt_unique_list[i]
            color = None
            try:
                color = self._tht_ttvt_maker.ttvt_dict[ttvt.lower()][SC.K_COLOR]
            except Exception:
                LoggerUtil.get_logger().warning(
                    f'Bc MPD write_data_to_excel_all_header_list No color found for TTVT {ttvt}, using default color')
                color = T.RGBA_COLORS_L[i % len(T.RGBA_COLORS_L)]
            color = T.lighten_color_rgba(color, 0.6)
            color = color[:-2].replace("#", "") #-#,a

            fill = openpyxl.styles.PatternFill(
                start_color=color, end_color=color, fill_type="solid"
            )

            ttvt_index = req_row_dic[SC.K_TTVT_2]
            for row in ws.iter_rows(
                min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column
            ):
                if str(row[ttvt_index].value).lower() == ttvt.lower():
                    has_cb = False
                    for cell in row:
                        if cell.value and "cb:" in str(cell.value).lower():
                            cell.font = Font(name="Times New Roman", color="FF0000")  # Normal, red
                            has_cb = True
                    if not has_cb:
                        for cell in row:
                            cell.fill = fill

        wb.save(self._excel_output_path)
        wb.close()

    def _write_data_to_excel_bc_tong_hop_sheet(self, data_bc_tghop: DataBcTgHop, sheet_name):
        #
        wb = openpyxl.load_workbook(self._excel_output_path)
        ws = wb[sheet_name]

        # Report title
        ws.cell(row=2, column= 2).value = "Thời gian " +\
            DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_FROM) + \
            " - " + DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TO)
        ws.cell(row=2, column= 2).font = T.EX_FORMAT_TITLE_FONT

        current_row = 6
        ### CANHBAO_CLR
        header_index_dict = {
            SC.K_UI_DON_VI_QUAN_LY: 1,
            SC.K_TTVT_2: 2,
            SC.K_UI_SO_LAN: 3,
            SC.K_UI_THOI_GIAN: 4
        }
        for item in data_bc_tghop.cbao_clr_item_list:
            current_row += 1

            for header, col_index in header_index_dict.items():
                ws.cell(row=current_row, column=col_index).value = item[header]

                #format:
                ws.cell(row=current_row, column=col_index).border = T.EX_FORMAT_THIN_BORDER
                if header in [SC.K_UI_SO_LAN, SC.K_UI_THOI_GIAN]:
                    ws.cell(row=current_row, column=col_index).alignment = \
                        T.EX_FORMAT_ALIGNMENT_RIGHT
                if current_row == 7:
                    ws.cell(row=current_row, column=col_index).font = T.EX_FORMAT_BOLD_FONT

        ### CANHBAO_NCLR
        current_row += 3
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)
        ws.cell(row=current_row, column=1).value = "CẢNH BÁO MÁY PHÁT ĐIỆN CHƯA KHÔI PHỤC"
        ws.cell(row=current_row, column=1).font = T.EX_FORMAT_TITLE_FONT_12
        ws.cell(row=current_row, column=1).alignment = T.EX_FORMAT_ALIGNMENT_CENTER

        # header
        current_row += 1
        ws.merge_cells(
            start_row=current_row, start_column=1, end_row=current_row+1, end_column=1)
        ws.cell(row=current_row, column=1).value = SC.K_UI_DON_VI_QUAN_LY
        T.format_header_cell(ws.cell(row=current_row, column=1))
        T.format_header_cell(ws.cell(row=current_row+1, column=1))

        ws.merge_cells(
            start_row=current_row, start_column=2, end_row=current_row+1, end_column=2)
        ws.cell(row=current_row, column=2).value = SC.K_TTVT_2
        T.format_header_cell(ws.cell(row=current_row, column=2))
        T.format_header_cell(ws.cell(row=current_row+1, column=2))

        ws.merge_cells(
            start_row=current_row, start_column=3, end_row=current_row+1, end_column=4)
        ws.cell(row=current_row, column=3).value = SC.K_UI_CBAO_NCLR
        for r in range(current_row, current_row+2):
            for c in range(3, 5):
                T.format_header_cell(ws.cell(row=r, column=c))
        #
        current_row +=1
        begin_row = current_row+1
        for item in data_bc_tghop.cbao_nclr_item_list:
            current_row += 1
            ws.merge_cells(
                start_row=current_row, start_column=3, end_row=current_row, end_column=4)

            ws.cell(row=current_row, column=1).value = item[SC.K_UI_DON_VI_QUAN_LY]
            ws.cell(row=current_row, column=2).value = item[SC.K_TTVT_2]
            ws.cell(row=current_row, column=3).value = item[SC.K_UI_CBAO_NCLR]

        # --- set format ---
        for row in ws.iter_rows(
                min_row=begin_row, max_row=ws.max_row, min_col=1, max_col=4):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER

                try:
                    float(cell.value)
                    cell.alignment = T.EX_FORMAT_ALIGNMENT_CENTER
                except:
                    pass

                if cell.row == begin_row:
                    cell.font = T.EX_FORMAT_BOLD_FONT

        wb.save(self._excel_output_path)
        wb.close()