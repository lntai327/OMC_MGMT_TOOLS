from collections import defaultdict
from datetime import datetime, timedelta, timezone #date,
import os
import re
from typing import DefaultDict
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.drawing.image import Image
import shutil
import os
from pathlib import Path
from openpyxl.styles import Font
# import sys
from dateutil import parser
import matplotlib
# Use a non-GUI backend to avoid starting a Matplotlib GUI from background threads
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import locale

from backend.constant import type as T
from backend.constant import excel_struct_info as ESI
from backend.util.ex_handle_util import ExcelHandleUtil
from backend.util.database_util import DatabaseFactory
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil
from share.constant import constant as SC
from share.constant import type as ST
from share.util.convert import to_float

class DataBcCbaoMllXgStruct:
    def __init__(self,
                 bc_chi_tiet_mll_tat_ca_nn_item_list = None,
                 bc_mll_nguon_td_item_list = None,
                 bc_tghop_bang_tghop_mll_item_list = None,
                 bc_tghop_bang_tghop_mll_da_loai_tru_item_list = None):

        self.bc_chi_tiet_mll_tat_ca_nn_item_list = \
                bc_chi_tiet_mll_tat_ca_nn_item_list \
                if bc_chi_tiet_mll_tat_ca_nn_item_list is not None else []
        self.bc_mll_nguon_td_item_list = \
                bc_mll_nguon_td_item_list \
                if bc_mll_nguon_td_item_list is not None else []
        self.bc_tghop_bang_tghop_mll_item_list = bc_tghop_bang_tghop_mll_item_list
        self.bc_tghop_bang_tghop_mll_da_loai_tru_item_list = bc_tghop_bang_tghop_mll_da_loai_tru_item_list

    # def __str__(self):
    #     return (
    #         f"Loai BTS: {self.he_thong}, "
    #         f"Excel output name: {self.excel_output_path}, "
    #         f"Chi tiet MLL: {self.bc_chi_tiet_mll_tat_ca_nn_item_list}, "
    #         f"Nguon TD: {self.bc_mll_nguon_td_item_list}"
    #     )

class ExcelBcCbaoMllWriter:
    def __init__(self):
        self._cr_time = datetime.now(timezone(timedelta(hours=7))).strftime("%H%M%S")
        self._db_adapter = DatabaseFactory.create_adapter()
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._tht_ttvt_maker.load()

        self._output_folder_path = ExplorerUtil().create_outfolder_fromtotime()

    def _write_data_to_excel_by_header(self, sheet_opened: Worksheet, row_index, header_dict, data_dict: dict):
        for header in header_dict.keys():
            sheet_opened.cell(row=row_index, column=header_dict[header]).value = data_dict.get(header, "")
            T.format_normal_cell(sheet_opened.cell(row=row_index, column=header_dict[header]))

    def _cal_tong_row(self, tong_hop_item_list: list):
        tong_so_bts = sum(
            [item[SC.K_UI_TONG_SO_BTS] for item in tong_hop_item_list]
        )
        su_co_mll_lan = sum(
            [item[SC.K_UI_SCO_MLL_LAN] for item in tong_hop_item_list]
        )
        thoi_gian_cbao_phut = sum(
            [item[SC.K_UI_TGIAN_CBAO_PHUT] for item in tong_hop_item_list]
        )

        binh_quan_phut_lan = 0 if su_co_mll_lan == 0 else round(
            thoi_gian_cbao_phut / su_co_mll_lan, 2
        )
        binh_quan_phut_bts = 0 if tong_so_bts == 0 else round(
            thoi_gian_cbao_phut / tong_so_bts, 2
        )
        return tong_so_bts, su_co_mll_lan, thoi_gian_cbao_phut, \
               binh_quan_phut_lan, binh_quan_phut_bts

    def _write_data_to_excel_bc_tong_hop_sheet(
            self, he_thong, excel_path, sheet_name, data: DataBcCbaoMllXgStruct):
        #
        dynamic_info_util = DynamicInfoUtil()
        rp_time_from = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_FROM)
        rp_time_to = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TO)
        rp_time_from_compare = dynamic_info_util.get_value(
            2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_FROM_CPARE
        )
        rp_time_to_compare = dynamic_info_util.get_value(
            2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TO_CPARE
        )

        wb = openpyxl.load_workbook(excel_path)
        ws = wb[sheet_name]

        #Report title
        ws.cell(row=1, column= 2).value = SC.K_EXCEL_BC_CBAO_MLL_TITLE + f' {he_thong}'
        ws.cell(row=1, column= 2).font = T.EX_FORMAT_TITLE_FONT

        ws.cell(row=2, column= 2).value = \
            "Thời gian " + rp_time_from + " - " + rp_time_to
        ws.cell(row=2, column= 2).font = T.EX_FORMAT_TITLE_FONT

        #############################################
        header_index_dict = {
            SC.K_UI_DON_VI_QUAN_LY: 1, SC.K_TTVT_2: 2, SC.K_UI_TONG_SO_BTS: 3,
            SC.K_UI_SCO_MLL_LAN: 4, SC.K_UI_TGIAN_CBAO_PHUT: 5, SC.K_UI_BINH_QUAN_PHUT_LAN: 6,
            SC.K_UI_TY_LE_PHUT_BTS: 7, SC.K_UI_TG_SO_BTS_TGGIAM_TRAM: 8,
            SC.K_UI_SU_CO_MLL_TGGIAM_LAN: 9, SC.K_UI_THGIAN_CBAO_TGGIAM_PHUT: 10,
            SC.K_UI_BINH_QUAN_TGGIAM_PHUT_LAN: 11, SC.K_UI_TY_LE_TGGIAM_PHUT_BTS: 12
        }

        ### BẢNG TỔNG HỢP MẤT LIÊN LẠC
        current_row = 7
        ws.cell(row=current_row, column=3).value = \
            dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE) +\
            " " +\
            dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME) +\
            f'({rp_time_from} - {rp_time_to})'
        ws.cell(row=current_row, column=3).font = T.EX_FORMAT_BOLD_FONT

        ws.cell(row=current_row, column=8).value = \
            dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE) +\
            " " +\
            dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE_BC_MLL) +\
            f'({rp_time_from_compare} - {rp_time_to_compare})'
        ws.cell(row=current_row, column=8).font = T.EX_FORMAT_BOLD_FONT

        current_row = 8
        for item in data.bc_tghop_bang_tghop_mll_item_list:
            current_row += 1
            row_data = [item.get(header, SC.K_UI_MSG_MISS_DB) for header in header_index_dict.keys()]
            ws.append(row_data)

        # --- set format ---
        for row in ws.iter_rows(
                min_row=9, max_row=current_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER

                if cell.col_idx in range(3, ws.max_column + 1):
                    cell.alignment = T.EX_FORMAT_ALIGNMENT_RIGHT

        #
        current_row += 1
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=2)
        ws.cell(row=current_row, column=1).value = "Tổng"
        #Tong so BTS, Su co MLL lan, Thoi gian cbao phut, Binh quan phut lan, Binh quan phut bts
        ws.cell(row=current_row, column=3).value, \
        ws.cell(row=current_row, column=4).value, \
        ws.cell(row=current_row, column=5).value, \
        ws.cell(row=current_row, column=6).value, \
        ws.cell(row=current_row, column=7).value = self._cal_tong_row(
            data.bc_tghop_bang_tghop_mll_item_list
        )
        for col in range(1, ws.max_column + 1): #Format
            ws.cell(row=current_row, column=col).border = T.EX_FORMAT_THIN_BORDER
            ws.cell(row=current_row, column=col).font = T.EX_FORMAT_BOLD_FONT

            if col == 1:
                ws.cell(row=current_row, column=col).alignment = T.EX_FORMAT_ALIGNMENT_CENTER
                continue
            if col in range(3, ws.max_column + 1):
                ws.cell(row=current_row, column=col).alignment = T.EX_FORMAT_ALIGNMENT_RIGHT

        ### BẢNG MẤT LIÊN LẠC DO NGUỒN (ĐÃ LOẠI TRỪ LOẠI 3 KHÔNG MPĐ) VÀ TRUYỀN DẪN
        # header
        current_row += 2
        ExcelHandleUtil().copy_rows_with_formatting(
            ws,
            5, 8,
            1, 12,
            current_row, 1
        )
        ws.cell(row=current_row, column=1).value = \
            "BẢNG MẤT LIÊN LẠC DO NGUỒN (ĐÃ LOẠI TRỪ LOẠI 3 KHÔNG MPĐ) VÀ TRUYỀN DẪN"

        data
        current_row += 3
        current_row_format = current_row + 1
        for item in data.bc_tghop_bang_tghop_mll_da_loai_tru_item_list:
            current_row += 1
            row_data = [item.get(header, SC.K_UI_MSG_MISS_DB) for header in header_index_dict.keys()]
            ws.append(row_data)

        # --- set format ---
        for row in ws.iter_rows(
                min_row=current_row_format, max_row=current_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER

                if cell.col_idx in range(3, ws.max_column + 1):
                    cell.alignment = T.EX_FORMAT_ALIGNMENT_RIGHT

        #
        current_row += 1
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=2)
        ws.cell(row=current_row, column=1).value = "Tổng"
        #Tong so BTS, Su co MLL lan, Thoi gian cbao phut, Binh quan phut lan, Binh quan phut bts
        ws.cell(row=current_row, column=3).value, \
        ws.cell(row=current_row, column=4).value, \
        ws.cell(row=current_row, column=5).value, \
        ws.cell(row=current_row, column=6).value, \
        ws.cell(row=current_row, column=7).value = self._cal_tong_row(
            data.bc_tghop_bang_tghop_mll_da_loai_tru_item_list
        )
        for col in range(1, ws.max_column + 1):
            ws.cell(row=current_row, column=col).border = T.EX_FORMAT_THIN_BORDER
            ws.cell(row=current_row, column=col).font = T.EX_FORMAT_BOLD_FONT

            if col == 1:
                ws.cell(row=current_row, column=col).alignment = T.EX_FORMAT_ALIGNMENT_CENTER
                continue
            if col in range(3, ws.max_column + 1):
                ws.cell(row=current_row, column=col).alignment = T.EX_FORMAT_ALIGNMENT_RIGHT

        #
        wb.save(excel_path)
        wb.close()

    def _write_data_to_excel_all_header_list(self, excel_path, sheet_name, sheet_info, data_list):
        ttvt_unique_list = []

        wb = openpyxl.load_workbook(excel_path)
        ws = wb[sheet_name]
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
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(start_header_list)):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER
                cell.font = T.EX_FORMAT_NORMAL_FONT

        req_row_dic = dict(zip(start_req_header_list, start_req_header_indices_list))
        for i in range(len(ttvt_unique_list)):
            ttvt: str = str(ttvt_unique_list[i])
            color = None
            try:
                color = self._tht_ttvt_maker.ttvt_dict[ttvt.lower()][SC.K_COLOR]
            except Exception:
                LoggerUtil.get_logger().warning(
                    f'_write_data_to_excel_all_header_list No color found for TTVT {ttvt}, using default color')
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
                    red_text_row = False

                    for cell in row:
                        cell_val = str(cell.value).strip().lower()

                        if cell.value and "cb:" in str(cell.value).lower():
                            cell.font = Font(name="Times New Roman", color="FF0000")  # Normal, red

                        #
                        if cell_val and ("fms" in cell_val):
                            red_text_row = True

                        #
                        cell.fill = fill

                    if red_text_row:
                        for cell in row:
                            cell.font = Font(name="Times New Roman", color="FF0000")  # Normal, red


        #
        wb.save(excel_path)
        wb.close()

    def _create_output(self, he_thong):
        dynamic_info_util = DynamicInfoUtil()
        rp_time_type = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE)
        rp_time = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME)
        site: str = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        if site.lower() == ST.Site.ALL_SITE.value:
            site = "2Site"

        match rp_time_type:
            case ST.TimeType.WEEK.value:
                rp_time_type = "Tuan"
            case ST.TimeType.MONTH.value:
                rp_time_type = "Thang"

        excel_output_template_path = \
                    ExplorerUtil().get_output_template_file_path(SC.K_EXCEL_BC_CBAO_MLL_TEMPLATE)

        excel_bc_cbao_mll_xg_name = \
            SC.K_EXCEL_BC_CBAO_MLL_NAME + \
            "_" + \
            he_thong + \
            "_" + \
            rp_time_type + rp_time + \
            "_" + \
            site + \
            "_" + \
            self._cr_time + \
            ".xlsx"

        excel_path = os.path.join(
            self._output_folder_path, excel_bc_cbao_mll_xg_name
        )

        shutil.copy(
            excel_output_template_path, excel_path
        )

        return excel_path

    # CHART for DO NGUỒN (ĐÃ LOẠI TRỪ LOẠI 3 KHÔNG MPĐ) VÀ TRUYỀN DẪN
    def _create_chart_chi_tieu_x(self, he_thong, data: DataBcCbaoMllXgStruct, chi_tieu: str):
        dynamic_info_util = DynamicInfoUtil()
        site: str = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        rp_time_type = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE)
        rp_time_from = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_FROM)
        year = parser.parse(rp_time_from).year

        row_keys_dict = {
            SC.K_HE_THONG: he_thong,
            SC.K_NAM: year,
            SC.K_RP_TIME_TYPE: rp_time_type
        }
        db_row_list = self._db_adapter.get_rows_list_by_value(
            SC.K_TABLE_BC_BTS_MLL_TGHOP_DA_LOAI_TRU,
            row_keys_dict
        )

        # Get latest rp_time_cpare_number time points for each TTVT
        rp_time_cpare_number: int = dynamic_info_util.get_value(
            2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE_NUMBER
        )
        rp_time_cpare_number = int(rp_time_cpare_number)
        db_row_list_ttvt_dict = defaultdict(list)
        for row in db_row_list:
            ttvt: str = str(row[SC.K_TTVT])
            ret_site = self._tht_ttvt_maker.ttvt_dict[ttvt.lower()][SC.K_SITE1]
            if (site.lower() != ST.Site.ALL_SITE.value) and (ret_site.lower() != site.lower()):
                continue
            db_row_list_ttvt_dict[ttvt].append(row)
        for k, v in db_row_list_ttvt_dict.items():
            if isinstance(v, list) and (len(v) > rp_time_cpare_number):
                v = sorted(v, key=lambda x: to_float(x[SC.K_RP_TIME]))
                db_row_list_ttvt_dict[k] = v[-rp_time_cpare_number:]
        db_row_list = []
        for k, v in db_row_list_ttvt_dict.items():
            db_row_list.extend(v)

        #
        x_axis = [] #thời gian Tuần / Tháng
        y_axis_dict = {} #TTVT : RP_TIME : giá trị Chỉ tiêu

        for row in db_row_list:
            if row[SC.K_RP_TIME] not in x_axis:
                x_axis.append(row[SC.K_RP_TIME])

            if row[SC.K_TTVT] not in y_axis_dict:
                y_axis_dict[row[SC.K_TTVT]] = {}
            y_axis_dict[row[SC.K_TTVT]][row[SC.K_RP_TIME]] = row[chi_tieu]
        x_axis.sort(key=int)

        locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')
        y_axis_dict = dict(
            sorted(y_axis_dict.items(), key=lambda x: locale.strxfrm(x[0]))
        )
        for ttvt in list(y_axis_dict.keys()):
            chi_tieu_dict = y_axis_dict[ttvt]
            chi_tieu_dict = dict(
                sorted(chi_tieu_dict.items(), key=lambda x: locale.strxfrm(x[0]))
            )
            y_axis_dict[ttvt] = chi_tieu_dict

        if not x_axis or not y_axis_dict:
            LoggerUtil.get_logger().warning(f'No data to plot for {chi_tieu}')
            return None

        # Plot
        plt.figure(figsize=(
            10, #max(10, 2*len(x_axis)),
            6
        ))

        for i, (ttvt, y_data_dict) in enumerate(y_axis_dict.items()):
            y_axis = []
            color = None
            try:
                color = self._tht_ttvt_maker.ttvt_dict[str(ttvt).lower()][SC.K_COLOR]
            except Exception:
                LoggerUtil.get_logger().warning(
                    f'_create_chart_chi_tieu_x No color found for TTVT {ttvt}, using default color')
                color = T.RGBA_COLORS_L[i % len(T.RGBA_COLORS_L)]
            for x in x_axis:
                if x not in y_data_dict.keys():
                    y_axis.append(np.nan)
                else:
                    # ensure numeric values when possible
                    try:
                        y_axis.append(int(y_data_dict[x]))
                    except Exception:
                        y_axis.append(np.nan)

            plt.plot(
                x_axis, y_axis,
                marker=T.PLOT_MARKERS_L[i % len(T.PLOT_MARKERS_L)],
                linestyle=T.PLOT_LINE_STYLES_L[i % len(T.PLOT_LINE_STYLES_L)],
                color=color,
                label=f'{ttvt}'
            )

            # Add value labels on plot points
            ax = plt.gca()
            for x_idx, (x_val, y_val) in enumerate(zip(x_axis, y_axis)):
                if not np.isnan(y_val):
                    ax.text(x_idx, y_val, f'{y_val}',
                            ha='center', va='bottom', fontsize=8, color=color)

        # Add labels, title, and legend
        full_chi_tieu_name = ""
        match chi_tieu:
            case SC.K_SCO_MLL_LAN:
                full_chi_tieu_name = "Sự Cố Mất Liên Lạc (Lần)"
            case SC.K_TGIAN_CBAO_PHUT:
                full_chi_tieu_name = "Thời Gian Mất Liên Lạc (Phút)"

        plt.xlabel(rp_time_type, fontweight='bold')
        plt.ylabel(full_chi_tieu_name, fontweight='bold')
        full_site_name = ""
        match site.lower():
            case ST.Site.DONG.value:
                full_site_name = "Site Bình Định"
            case ST.Site.TAY.value:
                full_site_name = "Site Gia Lai"
            case ST.Site.ALL_SITE.value:
                full_site_name = "Tất Cả Site"

        title_text = f'Biểu Đồ {full_chi_tieu_name}\n{full_site_name}'.upper()
        plt.title(title_text, fontweight='bold', color='red')
        ax = plt.gca()
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), ncol=1, fontsize='small', handlelength=5.0)
        # Give room on the right side for the legend
        plt.subplots_adjust(right=0.78)

        try:
            all_y = []
            for _, y_data_dict in y_axis_dict.items():
                for x in x_axis:
                    value = y_data_dict.get(x, None)
                    try:
                        all_y.append(int(value))
                    except Exception:
                        continue

            if len(all_y) > 0:
                y_min = int(np.nanmin(all_y))
                y_max = int(np.nanmax(all_y))
                # add a small margin
                if y_min == y_max:
                    margin = 1
                    y_min -= margin
                    y_max += margin
                else:
                    margin = (y_max - y_min) * 0.05
                    y_min -= margin
                    y_max += margin
                ax.set_ylim(y_min, y_max)
            else:
                # no numeric data, ensure 0 baseline visible
                ax.set_ylim(0, 1)

        except Exception:
            pass

        # Save chart as image
        chart_name = f"{he_thong} {str(chi_tieu).replace('\n', '')} {site}.png"
        chart_file_path = ExplorerUtil().get_cache_file_path(chart_name)
        chart_dir_path = os.path.dirname(chart_file_path)
        if chart_dir_path:
            Path(chart_dir_path).mkdir(parents=True, exist_ok=True)
        # Use bbox_inches='tight' to automatically include the legend placed
        # outside the axes when saving the figure
        plt.savefig(chart_file_path, bbox_inches='tight')
        plt.close()

        return chart_file_path

    def _write_data_to_excel_bdo_tke_sheet(
            self, he_thong, excel_path, sheet_name, data: DataBcCbaoMllXgStruct):
        #
        wb = openpyxl.load_workbook(excel_path)
        ws = wb[sheet_name]

        dsach_chi_tieu_list = [
            SC.K_SCO_MLL_LAN,
            SC.K_TGIAN_CBAO_PHUT
        ]

        current_row = 5
        for chi_tieu in dsach_chi_tieu_list:
            chart_file_path = self._create_chart_chi_tieu_x(he_thong, data, chi_tieu)
            if chart_file_path:
                img = Image(chart_file_path)
                ws.add_image(img, f'A{current_row}')
                current_row += 33

        wb.save(excel_path)
        wb.close()

    def write_excel_clr(
        self,
        data_dict: DefaultDict[str, DataBcCbaoMllXgStruct]
    ) -> str|None:
        #
        for he_thong, item in data_dict.items():
            excel_output_path = self._create_output(he_thong)
            #
            sheet_info = ESI.EXCEL_STRUCT_INFO[SC.K_EXCEL_BC_CBAO_MLL_KEY][SC.K_SHEET_INFO]\
                [SC.K_SHEET_BC_CHI_TIET_MLL_TCA_NNHAN]
            self._write_data_to_excel_all_header_list(
                excel_output_path, SC.K_SHEET_BC_CHI_TIET_MLL_TCA_NNHAN, sheet_info,
                item.bc_chi_tiet_mll_tat_ca_nn_item_list
            )
            #
            sheet_info = ESI.EXCEL_STRUCT_INFO[SC.K_EXCEL_BC_CBAO_MLL_KEY][SC.K_SHEET_INFO]\
                [SC.K_SHEET_BC_MLL_NGUON_TD]
            self._write_data_to_excel_all_header_list(
                excel_output_path,
                SC.K_SHEET_BC_MLL_NGUON_TD,
                sheet_info,
                item.bc_mll_nguon_td_item_list
            )
            #
            self._write_data_to_excel_bc_tong_hop_sheet(
                he_thong,
                excel_output_path,
                SC.K_SHEET_BAO_CAO_TONG_HOP,
                item
            )
            self._write_data_to_excel_bdo_tke_sheet(
                he_thong,
                excel_output_path,
                SC.K_SHEET_BDO_TKE,
                item
            )

        return self._output_folder_path

    def _make_db_item(self, he_thong, data_dict: dict):
        dynamicInfoUtil = DynamicInfoUtil()
        rp_time_type = dynamicInfoUtil.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE)
        rp_time = dynamicInfoUtil.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME)
        rp_time_from = dynamicInfoUtil.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_FROM)
        rp_time_to = dynamicInfoUtil.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TO)

        item = {
            SC.K_DVI_QLY: str(data_dict[SC.K_UI_DON_VI_QUAN_LY]).strip(),
            SC.K_TTVT: str(data_dict[SC.K_TTVT_2]).strip(),
            SC.K_TONG_SO_BTS: str(data_dict[SC.K_UI_TONG_SO_BTS]).strip(),
            SC.K_SCO_MLL_LAN: str(data_dict[SC.K_UI_SCO_MLL_LAN]).strip(),
            SC.K_TGIAN_CBAO_PHUT: str(data_dict[SC.K_UI_TGIAN_CBAO_PHUT]).strip(),
            SC.K_BINH_QUAN_PHUT_LAN: str(data_dict[SC.K_UI_BINH_QUAN_PHUT_LAN]).strip(),
            SC.K_TY_LE_PHUT_BTS: str(data_dict[SC.K_UI_TY_LE_PHUT_BTS]).strip(),

            SC.K_HE_THONG: str(he_thong).strip(),
            SC.K_NAM: str(parser.parse(rp_time_from).year).strip(),
            SC.K_RP_TIME_TYPE: str(rp_time_type).strip(),
            SC.K_RP_TIME: str(rp_time).strip(),
            SC.K_RP_TIME_FROM: str(rp_time_from).strip(),
            SC.K_RP_TIME_TO: str(rp_time_to).strip()
        }

        return item

    def write_db(self, data_dict: DefaultDict[str, DataBcCbaoMllXgStruct]) -> None:
        for he_thong, item in data_dict.items():
            bc_tghop_bang_tghop_mll_db_item_list = []
            bc_tghop_bang_tghop_mll_da_loai_tru_db_item_list = []

            for i in item.bc_tghop_bang_tghop_mll_item_list:
                ret = self._make_db_item(he_thong, i)
                bc_tghop_bang_tghop_mll_db_item_list.append(ret)

            for i in item.bc_tghop_bang_tghop_mll_da_loai_tru_item_list:
                ret = self._make_db_item(he_thong, i)
                bc_tghop_bang_tghop_mll_da_loai_tru_db_item_list.append(ret)

            self._db_adapter.write_to_db(SC.K_TABLE_BC_BTS_MLL_TGHOP,\
                                   bc_tghop_bang_tghop_mll_db_item_list)

            self._db_adapter.write_to_db(SC.K_TABLE_BC_BTS_MLL_TGHOP_DA_LOAI_TRU,\
                                   bc_tghop_bang_tghop_mll_da_loai_tru_db_item_list)

    def _write_excel_mll_bts_ttvtx_nclr(
                                        self,
                                        excel_path,
                                        data_list: list
                                    ):
        data_list_ttvt_dict = defaultdict(list)
        for item in data_list:
            data_list_ttvt_dict[item[SC.K_TTVT_2]].append(item)

        sheet_info = ESI.EXCEL_STRUCT_INFO[SC.K_BC_CBAO_MLL_NCLR][SC.K_SHEET_INFO]['MLL BTS TTVT X']

        for ttvt, data_list in data_list_ttvt_dict.items():
            if re.search("Trung tâm Viễn thông", ttvt, re.IGNORECASE):
                sheet_name = f'MLL BTS TTVT {ttvt[21:].strip()}'
            else:
                sheet_name = f'MLL BTS TTVT UNKNOWN'

            wb = openpyxl.load_workbook(excel_path)
            template_sheet = wb['MLL BTS TTVT X']
            ws = wb.copy_worksheet(template_sheet)
            ws.title = sheet_name
            ws.sheet_state = 'visible'
            ws.sheet_view.showGridLines = False
            wb.save(excel_path)
            wb.close()

            self._write_data_to_excel_all_header_list(excel_path, sheet_name, sheet_info, data_list)

    def _write_excel_cbao_mat_ac_nclr(
                                        self,
                                        excel_path,
                                        data_list: list
                                    ):
        sheet_name = 'CANHBAO_MATAC'
        sheet_info = ESI.EXCEL_STRUCT_INFO[SC.K_BC_CBAO_MLL_NCLR][SC.K_SHEET_INFO][sheet_name]
        self._write_data_to_excel_all_header_list(excel_path, sheet_name, sheet_info, data_list)

    def _write_excel_csht_mll_nclr(
                                        self,
                                        excel_path,
                                        data_list: list
                                    ):
        sheet_name = 'CSHT Mất liên lạc'
        sheet_info = ESI.EXCEL_STRUCT_INFO[SC.K_BC_CBAO_MLL_NCLR][SC.K_SHEET_INFO][sheet_name]
        self._write_data_to_excel_all_header_list(excel_path, sheet_name, sheet_info, data_list)

    def _write_excel_bc_tghop_nclr(
                                    self,
                                    excel_path,
                                    data_list: list
                                ):
        sheet_name = SC.K_SHEET_BAO_CAO_TONG_HOP
        wb = openpyxl.load_workbook(excel_path)
        ws = wb[sheet_name]

        dynamic_info_util = DynamicInfoUtil()

        #data src
        data_src = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SRC_DATA)
        ws.cell(row=2, column=3).value = data_src
        ws.cell(row=2, column= 3).font = Font( # Black color, bold
            bold=True, color="000000", size=12, name="Times New Roman",
            italic=True
        )

        #thoi gian bc hien tai
        ws.cell(row=8, column=3).value = str(data_src)\
            .translate(str.maketrans('', '', '()'))

        #thoi gian bc so sanh
        need_compare = dynamic_info_util.get_value(
            2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT
        )
        if need_compare == "1":
            time_cpare = dynamic_info_util.get_value(
                2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE)
            time_cpare = str(time_cpare)\
                .translate(str.maketrans('', '', '()'))
            ws.cell(row=8, column= 10).value = time_cpare
        else:
            ExcelHandleUtil().remove_column(
                ws,
                10, 16
            )

        #Bang tong hop
        for item in data_list:
            row_data = [item.get(header, SC.K_UI_MSG_MISS_DB) for header in range(1, len(item)+1)]
            ws.append(row_data)

        # --- set format ---
        for row in ws.iter_rows(
                min_row=9, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER

                if cell.row == 11: #row tổng
                    cell.font = T.EX_FORMAT_BOLD_FONT

        #
        wb.save(excel_path)
        wb.close()

    def write_excel_nclr(
                            self,
                            data_bc_cbao_mll_xg_nclr_list: list,
                            data_bc_cbao_mat_ac_list: list,
                            data_bc_csht_mll_nclr_list,
                            data_bc_tghop_nclr_list
                        ) -> None:
        dynamic_info_util = DynamicInfoUtil()
        rp_time_type = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE)
        rp_time = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME)
        site: str = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        if site.lower() == ST.Site.ALL_SITE.value:
            site = "2Site"

        match rp_time_type:
            case ST.TimeType.WEEK.value:
                rp_time_type = "Tuan"
            case ST.TimeType.MONTH.value:
                rp_time_type = "Thang"

        excel_output_template_path = \
                    ExplorerUtil().get_output_template_file_path(SC.K_BC_CBAO_MLL_NCLR_TEMPLATE)

        excel_bc_cbao_mll_xg_name = \
            SC.K_EXCEL_BC_CBAO_MLL_NAME + "_NCLR"\
            "_" + \
            rp_time_type + rp_time + \
            "_" + \
            site + \
            "_" + \
            self._cr_time + \
            ".xlsx"

        excel_path = os.path.join(
            self._output_folder_path, excel_bc_cbao_mll_xg_name
        )

        shutil.copy(
            excel_output_template_path, excel_path
        )

        #
        self._write_excel_mll_bts_ttvtx_nclr(excel_path, data_bc_cbao_mll_xg_nclr_list)
        self._write_excel_cbao_mat_ac_nclr(excel_path, data_bc_cbao_mat_ac_list)
        self._write_excel_csht_mll_nclr(excel_path, data_bc_csht_mll_nclr_list)
        self._write_excel_bc_tghop_nclr(excel_path, data_bc_tghop_nclr_list)