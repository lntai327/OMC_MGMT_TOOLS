from collections import defaultdict
import locale
import os
import openpyxl
import shutil
from datetime import datetime, timedelta, timezone #date,
from openpyxl.styles import Font

from backend.constant import type as T
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.bc_bts.excel_nodeb3g_repo import ExcelNodeb3gService
from backend.repositories.bc_bts.excel_enodeb4g_repo import ExcelEnodeb4gService
from backend.repositories.bc_bts.excel_gnodeb5g_repo import ExcelGnodeb5gService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.repositories.bc_bts.excel_rp_al_chay_mpd_repo import ExcelRpAlMpdService
from backend.constant import excel_struct_info as ESI
from backend.util.ex_handle_util import ExcelHandleUtil

from share.util.explorer_util import ExplorerUtil
from share.constant import constant as SC
from share.constant import type as ST
from share.util.convert import safe_sort_date_time, safe_sort_value, to_int
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil

class BcChayMpdQuaBgsService:
    def __init__(self, ui_set_error_callback=None):
        locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')

        self._init_data()

        self._ui_set_error_callback = ui_set_error_callback

        self._csht_ccl_service = CshtCclService()
        self._nodeb3g_sheet_maker = ExcelNodeb3gService()
        self._enodeb4g_sheet_maker = ExcelEnodeb4gService()
        self._gnodeb5g_sheet_maker = ExcelGnodeb5gService()
        self._rp_alarm_maker = ExcelRpAlMpdService(ui_set_error_callback)
        self._tht_ttvt_maker = ExcelThtTtvtMaker()

    def _init_data(self):
        self._data_bc_chi_tiet_list = []
        self._data_bc_chi_tiet_nclr_list = []
        self._data_bc_tghop = DataBcTgHop([], [])

    def _prepare_data(self):
        self._csht_ccl_service.load()
        self._nodeb3g_sheet_maker.load()
        self._enodeb4g_sheet_maker.load()
        self._gnodeb5g_sheet_maker.load()
        self._rp_alarm_maker.load()
        self._tht_ttvt_maker.load()

        self._bts_all_items_ten_tren_hthong_dict = {}
        for item in self._gnodeb5g_sheet_maker.gnodeb5g_items_list_all:
            self._bts_all_items_ten_tren_hthong_dict[
                (item[SC.K_TEN_TREN_HE_THONG_COMPACT])
            ] = item

        for item in self._enodeb4g_sheet_maker.enodeb4g_items_list_all:
            self._bts_all_items_ten_tren_hthong_dict[
                (item[SC.K_TEN_TREN_HE_THONG_COMPACT])
            ] = item

        for item in self._nodeb3g_sheet_maker.nodeb3g_items_list_all:
            self._bts_all_items_ten_tren_hthong_dict[
                (item[SC.K_TEN_TREN_HE_THONG_COMPACT])
            ] = item

    def _make_data_bc_chi_tiet_item(self, item_dict):
        _item = {}
        _item[SC.K_STT] = 0
        _item[SC.K_NE] = item_dict[SC.K_TEN_NE]
        _item[SC.K_UI_TG_SU_CO2] = item_dict[SC.K_TG_SU_CO_1]
        _item[SC.K_UI_TG_CLR1] = item_dict[SC.K_TG_CLR]
        _item[SC.K_UI_TG_CBAO1] = to_int(item_dict[SC.K_TG_CBAO], force=False)
        _item[SC.K_UI_VNP_GHI_CHU1] = item_dict[SC.K_VNP_GHI_CHU]
        _item[SC.K_UI_TINH_GHI_CHU1] = item_dict[SC.K_TINH_GHI_CHU]
        _item[SC.K_UI_LOAI_SU_CO1] = item_dict[SC.K_LOAI_SU_CO]
        _item[SC.K_UI_TG_CBAO_AC] = item_dict[SC.K_TIME_AC]
        _item[SC.K_UI_PHAN_LOAI_TRAM] = item_dict[SC.K_PHAN_LOAI_TRAM]

        try:
            ma_csht = self._bts_all_items_ten_tren_hthong_dict\
                [(item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT])]\
                [SC.K_MA_CSHT]
            _item[SC.K_UI_TEN_TRAM] = self._bts_all_items_ten_tren_hthong_dict\
                [(item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT])]\
                [SC.K_TEN_QUAN_LY]
        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_NE}'
            LoggerUtil.get_logger().warning(
                f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet_item {_item[SC.K_NE]} {msg} {e}'
            )
            if self._ui_set_error_callback: self._ui_set_error_callback(_item[SC.K_NE], msg)
            ma_csht = SC.K_UI_MSG_MISS_DB
            _item[SC.K_UI_TEN_TRAM] = SC.K_UI_MSG_MISS_DB
            _item[SC.K_UI_DON_VI_QUAN_LY] = SC.K_UI_MSG_MISS_DB
            _item[SC.K_TTVT_2] = SC.K_UI_MSG_MISS_DB

            return _item

        if ma_csht == "":
            msg = f'{SC.K_UI_MSG_KGAN_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(_item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                (f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet_item failed {_item[SC.K_NE]} : {msg}'))
            _item[SC.K_UI_DON_VI_QUAN_LY] = SC.K_UI_MSG_MISS_DB
            _item[SC.K_TTVT_2] = SC.K_UI_MSG_MISS_DB
            return _item

        try:
            _item[SC.K_UI_DON_VI_QUAN_LY] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[ma_csht][SC.K_TEN_DVI_QLY]
            _item[SC.K_TTVT_2] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[ma_csht][SC.K_TEN_TTVT_TRAM_VT_NETX]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                (f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet_item MACSHT key {e}'))
            msg = f'{SC.K_UI_MSG_KGAN_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(_item[SC.K_NE], msg)
            _item[SC.K_UI_DON_VI_QUAN_LY] = SC.K_UI_MSG_MISS_DB
            _item[SC.K_TTVT_2] = SC.K_UI_MSG_MISS_DB

        return _item

    def _sort_data_bc_chi_tiet(self, data_bc_chi_tiet_item_list):
        data_bc_chi_tiet_item_list_sorted = []

        # sort Đơn vị quản lý: to ha tang -> TTVT -> NE -> Thời gian sự cố
        data_bc_chi_tiet_item_list.sort(
            key=lambda x: (
                safe_sort_value(locale.strxfrm(x[SC.K_UI_DON_VI_QUAN_LY])),
                safe_sort_value(locale.strxfrm(x[SC.K_TTVT_2])),
                safe_sort_value(locale.strxfrm(x[SC.K_NE])),
                safe_sort_date_time(x[SC.K_UI_TG_SU_CO2], "%d/%m/%Y %H:%M:%S"),
            )
        )

        data_bc_chi_tiet_item_list_dvi_qly_dict = defaultdict(list)
        for item in data_bc_chi_tiet_item_list:
            data_bc_chi_tiet_item_list_dvi_qly_dict[item[SC.K_UI_DON_VI_QUAN_LY]].append(item)

        #sort site
        data_bc_chi_tiet_item_list_dvi_qly_dict_bdh = {}
        data_bc_chi_tiet_item_list_dvi_qly_dict_gli = {}
        data_bc_chi_tiet_item_list_dvi_qly_dict_x = {}

        for to_ha_tang, data_bc_chi_tiet_item_list_thtang_x in \
                data_bc_chi_tiet_item_list_dvi_qly_dict.items():
            try:
                site: str = self._tht_ttvt_maker.tht_dict[str(to_ha_tang).lower()][SC.K_SITE1]
                match site.lower():
                    case ST.Site.DONG.value:
                        data_bc_chi_tiet_item_list_dvi_qly_dict_bdh[to_ha_tang] = data_bc_chi_tiet_item_list_thtang_x
                    case ST.Site.TAY.value:
                        data_bc_chi_tiet_item_list_dvi_qly_dict_gli[to_ha_tang] = data_bc_chi_tiet_item_list_thtang_x
            except:
                LoggerUtil.get_logger().error(
                    f'BcChayMpdQuaBgsService _sort_data_bc_chi_tiet failed {to_ha_tang}')
                data_bc_chi_tiet_item_list_dvi_qly_dict_x[to_ha_tang] = data_bc_chi_tiet_item_list_thtang_x

        data_bc_chi_tiet_item_list_dvi_qly_dict = data_bc_chi_tiet_item_list_dvi_qly_dict_bdh | \
                                               data_bc_chi_tiet_item_list_dvi_qly_dict_gli | \
                                               data_bc_chi_tiet_item_list_dvi_qly_dict_x

        # output sorted
        for tht, item_list_ne_x in data_bc_chi_tiet_item_list_dvi_qly_dict.items():
            data_bc_chi_tiet_item_list_sorted.extend(item_list_ne_x)

        return data_bc_chi_tiet_item_list_sorted

    def _make_data_bc_chi_tiet(self): #& CBAO NCLR
        for item in self._rp_alarm_maker.rp_alarm_items_list_all:
            ret = self._make_data_bc_chi_tiet_item(item)

            if str(item[SC.K_TTHAI_CLR]).lower() == SC.K_CLR.lower():
                self._data_bc_chi_tiet_list.append(ret)
            else:
                ret[SC.K_UI_GHI_CHU] = "Đề nghị kiểm tra lại"
                self._data_bc_chi_tiet_nclr_list.append(ret)

        try:
            self._data_bc_chi_tiet_list = self._sort_data_bc_chi_tiet(self._data_bc_chi_tiet_list)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet sort _data_bc_chi_tiet_list failed due to {e}'
            )

        try:
            self._data_bc_chi_tiet_nclr_list = self._sort_data_bc_chi_tiet(self._data_bc_chi_tiet_nclr_list)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet sort _data_bc_chi_tiet_nclr_list failed due to {e}'
            )

    def _sort_data_table_bc_tghop(self, data_table_bc_tghop_list):
        data_table_bc_tghop_list_sorted = []

        # sort Đơn vị quản lý
        data_table_bc_tghop_list_dvi_qly_dict = defaultdict(list)
        for item in data_table_bc_tghop_list:
            data_table_bc_tghop_list_dvi_qly_dict[item[SC.K_UI_DON_VI_QUAN_LY]].append(item)
        data_table_bc_tghop_list_dvi_qly_dict = dict(
            sorted(
                data_table_bc_tghop_list_dvi_qly_dict.items(),
                key=lambda item: locale.strxfrm(item[0])
            )
        )
        for dvi_qly, data_table_bc_tghop_list_dvi_qly_x \
                in data_table_bc_tghop_list_dvi_qly_dict.items():
            # sort TTVT
            data_table_bc_tghop_list_dvi_qly_x.sort(
                key=lambda x: locale.strxfrm(x[SC.K_TTVT_2])
            )

            # output sorted
            data_table_bc_tghop_list_sorted.extend(data_table_bc_tghop_list_dvi_qly_x)

        return data_table_bc_tghop_list_sorted

    def _make_data_bc_tghop_clr_item(self, ttvt_dict):
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ttvt_dict[SC.K_TO_HA_TANG]
        item[SC.K_TTVT_2] = ttvt_dict[SC.K_TTVT]

        item[SC.K_UI_SO_LAN] = 0
        item[SC.K_UI_THOI_GIAN] = 0
        for v in self._data_bc_chi_tiet_list:
            if str(v[SC.K_TTVT_2]).lower() == str(item[SC.K_TTVT_2]).lower():
                item[SC.K_UI_SO_LAN] += 1
                try:
                    item[SC.K_UI_THOI_GIAN] += float(v[SC.K_UI_TG_CBAO1])
                except ValueError as e:
                    LoggerUtil.get_logger().warning(f'_make_data_bc_tghop_clr_item key {e}')

        return item

    def _make_data_bc_tghop_nclr_item(self, ttvt_dict):
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ttvt_dict[SC.K_TO_HA_TANG]
        item[SC.K_TTVT_2] = ttvt_dict[SC.K_TTVT]

        item[SC.K_UI_CBAO_NCLR] = 0
        for v in self._data_bc_chi_tiet_nclr_list:
            if str(v[SC.K_TTVT_2]).lower() == str(item[SC.K_TTVT_2]).lower():
                item[SC.K_UI_CBAO_NCLR] += 1

        return item

    def _make_data_bc_tghop(self):
        site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

        for ttvt_dict in self._tht_ttvt_maker.ttvt_list:
            if site.lower() == ST.Site.ALL_SITE.value:
                pass
            elif site.lower() not in str(ttvt_dict[SC.K_SITE1]).lower():
                continue

            self._data_bc_tghop.cbao_clr_item_list.append(
                self._make_data_bc_tghop_clr_item(ttvt_dict)
            )
            self._data_bc_tghop.cbao_nclr_item_list.append(
                self._make_data_bc_tghop_nclr_item(ttvt_dict)
            )

        # sort
        self._data_bc_tghop.cbao_clr_item_list = \
            self._sort_data_table_bc_tghop(self._data_bc_tghop.cbao_clr_item_list)
        self._data_bc_tghop.cbao_nclr_item_list = \
            self._sort_data_table_bc_tghop(self._data_bc_tghop.cbao_nclr_item_list)

        # make row Tổng
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ""
        item[SC.K_TTVT_2] = "Tổng"
        item[SC.K_UI_SO_LAN] = sum(
            [x[SC.K_UI_SO_LAN] for x in self._data_bc_tghop.cbao_clr_item_list])
        item[SC.K_UI_THOI_GIAN] = sum(
            [x[SC.K_UI_THOI_GIAN] for x in self._data_bc_tghop.cbao_clr_item_list]
        )
        self._data_bc_tghop.cbao_clr_item_list.insert(0, item)

        #
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ""
        item[SC.K_TTVT_2] = "Tổng"
        item[SC.K_UI_CBAO_NCLR] = sum(
            [x[SC.K_UI_CBAO_NCLR] for x in self._data_bc_tghop.cbao_nclr_item_list]
        )
        self._data_bc_tghop.cbao_nclr_item_list.insert(0, item)

    def make_bc_chay_mpd_qua_bgs(self) -> str|None:
        ret_path = None

        # init data
        self._init_data()
        # prepare data
        self._prepare_data()
        # make BC Chi Tiết & CANHBAO_NCLR
        self._make_data_bc_chi_tiet()
        # make BC Tong hop
        self._make_data_bc_tghop()

        writer = ExcelBcMpdWriter()
        ret_path = writer.write_excel(
            self._data_bc_chi_tiet_list,
            self._data_bc_chi_tiet_nclr_list,
            self._data_bc_tghop,
        )

        return ret_path

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