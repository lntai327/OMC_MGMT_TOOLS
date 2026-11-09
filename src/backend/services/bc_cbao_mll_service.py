from collections import defaultdict
import locale
import shutil
import os
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from backend.constant import type as T
from backend.repositories.bc_bts.excel_bc_cbao_mll.excel_bc_cbao_mll_maker import ExcelBcCbaoMllMaker
from backend.util.database_util import DatabaseFactory
# Fixed data
from backend.repositories.bc_bts.excel_nodeb3g.excel_nodeb3g_maker import ExcelNodeb3gSheetMaker
from backend.repositories.bc_bts.excel_enodeb4g.excel_enodeb4g_maker import ExcelEnodeb4gSheetMaker
from backend.repositories.bc_bts.excel_gnodeb5g.excel_gnodeb5g_maker import ExcelGnodeb5gSheetMaker
from backend.repositories.bc_bts.excel_dmoi_qly_csht.excel_dmoi_qly_csht_maker import ExcelDmoiQlyCshtMaker
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.repositories.bc_bts.cf_bts.cf_bts_maker import CFBtsMaker
# Input
from backend.repositories.bc_bts.excel_rp_alarm_cbao_mll.excel_rp_alarm_maker import ExcelRpAlarmCbaoMllMaker
# Output
from backend.repositories.bc_bts.excel_bc_cbao_mll.excel_bc_cbao_mll_writer import ExcelBcCbaoMllWriter, \
    DataBcCbaoMllXgStruct

from share.constant import constant as SC
from share.constant import type as ST
from share.session import Session
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.convert import safe_sort_date_time, safe_sort_value, to_int

class BcCbaoMllService:
    def __init__(self, ui_set_error_callback=None):
        locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')

        self._ui_set_error_callback = ui_set_error_callback
        self._init_data()

        self._db_adapter = DatabaseFactory.create_adapter()
        self._nodeb3g_sheet_maker = ExcelNodeb3gSheetMaker()
        self._enodeb4g_sheet_maker = ExcelEnodeb4gSheetMaker()
        self._gnodeb5g_sheet_maker = ExcelGnodeb5gSheetMaker()
        self._dmoi_qly_csht_maker = ExcelDmoiQlyCshtMaker()
        self._csht_ccl_service = CshtCclService()
        self._rp_al_cbao_mll_maker = ExcelRpAlarmCbaoMllMaker(ui_set_error_callback)
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._cf_bts_maker = CFBtsMaker()
        self._bc_nclr_maker = ExcelBcCbaoMllMaker()

    def _init_data(self):
        self._data_bc_cbao_mll_clr_xg_dict = defaultdict(DataBcCbaoMllXgStruct)
        self._data_bc_cbao_mll_bts_xg_nclr_list = []
        self._data_bc_mat_nguon_ac_nclr_list = []
        self._data_bc_csht_mll_nclr_list = []
        self._data_bc_tghop_nclr_list = []

        self._need_cpare_nclr = DynamicInfoUtil().get_value(
            2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT)

    def _prepare_data(self):
        self._nodeb3g_sheet_maker.load()
        self._enodeb4g_sheet_maker.load()
        self._gnodeb5g_sheet_maker.load()
        self._dmoi_qly_csht_maker.load()
        self._csht_ccl_service.load()
        self._rp_al_cbao_mll_maker.load()
        self._tht_ttvt_maker.load()
        self._cf_bts_maker.load()
        if self._need_cpare_nclr == '1':
            self._bc_nclr_maker.load()

        self._bts_all_items_ten_tren_hthong_dict = {}
        for item in self._gnodeb5g_sheet_maker.gnodeb5g_items_list_all:
            self._bts_all_items_ten_tren_hthong_dict[
                (item[SC.K_TEN_TREN_HE_THONG_COMPACT], T.HeThong._5G.value)
            ] = item

        for item in self._enodeb4g_sheet_maker.enodeb4g_items_list_all:
            self._bts_all_items_ten_tren_hthong_dict[
                (item[SC.K_TEN_TREN_HE_THONG_COMPACT], T.HeThong._4G.value)
            ] = item

        for item in self._nodeb3g_sheet_maker.nodeb3g_items_list_all:
            self._bts_all_items_ten_tren_hthong_dict[
                (item[SC.K_TEN_TREN_HE_THONG_COMPACT], T.HeThong._3G.value)
            ] = item

        self._bts_xg_ma_tram_dict = defaultdict(list)
        self._bts_xg_onair_items_list = \
            self._gnodeb5g_sheet_maker.gnodeb5g_items_list_all +\
            self._enodeb4g_sheet_maker.enodeb4g_items_list_all +\
            self._nodeb3g_sheet_maker.nodeb3g_items_list_all
        for item in self._bts_xg_onair_items_list:
            ma_tram = self._extract_ma_tram_from_ten_ne(item[SC.K_TEN_TREN_HE_THONG])
            self._bts_xg_ma_tram_dict[ma_tram].append(item)

    #***************************Define function************************#
    # Extract "Mã trạm" from "NE"
    def _extract_ma_tram_from_ten_ne(self, s: str):
        # Case 1: Mobiphone
        if len(s) == 6:
            return s

        # Case 2: orther
        if len(s) > 10:
            return s[3:3+6]

        return s

    def _is_item_of_bc_mll_nguon_td(self, item_dict: dict, he_thong: str) -> bool:
        if item_dict[SC.K_UI_LOAI_SU_CO1] not in [1, 5]:
            return False

        ne = item_dict[SC.K_NE]
        ne_compact = ne[2:].replace("-", "") if ne else ""

        try:
            if str(self._bts_all_items_ten_tren_hthong_dict\
                    [(ne_compact, he_thong)][SC.K_LOAI_TRAM]).lower() == \
                    "smallcell":
                return False
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _is_item_of_bc_mll_nguon_td failed ne: {ne} due to {e}'
            )

        try:
            if item_dict[SC.K_UI_LOAI_SU_CO1] == 1 \
                    and "3" in str(item_dict[SC.K_UI_PHAN_LOAI_TRAM]).lower() \
                    and str(item_dict[SC.K_UI_TRTHAI_DAT_MNO]).lower() == \
                        "không có":
                return False
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _is_item_of_bc_mll_nguon_td failed ne: {ne} due to {e}'
            )

        return True

    def _get_loai_nha_tram_csht_ccl(self, ma_csht: str) -> str|None:
        loai_nha_tram: str = str(
            self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                [ma_csht][SC.K_LOAI_NHA_TRAM]
        ).strip().lower()

        if "1" in loai_nha_tram:
            return "Trạm viễn thông loại 1"
        if "2" in loai_nha_tram:
            return "Trạm viễn thông loại 2"
        if "3" in loai_nha_tram:
            return "Trạm viễn thông loại 3"

        return ""

    def _sort_data_bc_chi_tiet(self, data_bc_chi_tiet_item_list):
        data_bc_chi_tiet_item_list_sorted = []

        # sort Tổ hạ tầng -> TTVT -> NE -> Thời gian sự cố
        data_bc_chi_tiet_item_list.sort(
            key=lambda x: (
                safe_sort_value(locale.strxfrm(x[SC.K_UI_TO_HA_TANG])),
                safe_sort_value(locale.strxfrm(x[SC.K_TTVT_2])),
                safe_sort_value(locale.strxfrm(x[SC.K_NE])),
                safe_sort_date_time(x[SC.K_UI_TG_SU_CO2], "%d/%m/%Y %H:%M:%S"),
            )
        )

        bc_chi_tiet_mll_list_to_ha_tang_dict = defaultdict(list)
        for item in data_bc_chi_tiet_item_list:
            bc_chi_tiet_mll_list_to_ha_tang_dict[item[SC.K_UI_TO_HA_TANG]].append(item)

        # sort site
        bc_chi_tiet_mll_list_to_ha_tang_dict_bdh = {}
        bc_chi_tiet_mll_list_to_ha_tang_dict_gli = {}
        bc_chi_tiet_mll_list_to_ha_tang_dict_nid = {}

        for to_ha_tang, data_bc_chi_tiet_item_list_thtang_x in \
                bc_chi_tiet_mll_list_to_ha_tang_dict.items():
            try:
                site: str = self._tht_ttvt_maker.tht_dict[str(to_ha_tang).lower()][SC.K_SITE1]
                match site.lower():
                    case ST.Site.DONG.value:
                        bc_chi_tiet_mll_list_to_ha_tang_dict_bdh[to_ha_tang] = data_bc_chi_tiet_item_list_thtang_x
                    case ST.Site.TAY.value:
                        bc_chi_tiet_mll_list_to_ha_tang_dict_gli[to_ha_tang] = data_bc_chi_tiet_item_list_thtang_x
            except:
                LoggerUtil.get_logger().error(
                    f'BcCbaoMllService _sort_data_bc_chi_tiet failed {to_ha_tang}')
                bc_chi_tiet_mll_list_to_ha_tang_dict_nid[to_ha_tang] = data_bc_chi_tiet_item_list_thtang_x

        bc_chi_tiet_mll_list_to_ha_tang_dict = bc_chi_tiet_mll_list_to_ha_tang_dict_bdh | \
                                               bc_chi_tiet_mll_list_to_ha_tang_dict_gli | \
                                               bc_chi_tiet_mll_list_to_ha_tang_dict_nid

        # output sorted
        for tht, item_list_ne_x in bc_chi_tiet_mll_list_to_ha_tang_dict.items():
            data_bc_chi_tiet_item_list_sorted.extend(item_list_ne_x)

        return data_bc_chi_tiet_item_list_sorted
    
    def _count_info_of_ttvt_x_clr(
                            self,
                            bts_xg_items_list_latest: list,
                            bc_chi_tiet_mll_x_item_list: list,
                            ttvt: str
    ):
        tong_so_bts = 0
        for item in bts_xg_items_list_latest:
            try:
                if str(self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                        [item[SC.K_MA_CSHT]][SC.K_TEN_TTVT_TRAM_VT_NETX]).lower() == \
                        ttvt.lower():
                    tong_so_bts += 1
            except KeyError as e:
                LoggerUtil.get_logger().warning(
                    f'BcCbaoMllService _count_info_of_ttvt_x_clr: tong_so_bts failed {e}')

        sco_mll_lan = sum(
            [1 for item in bc_chi_tiet_mll_x_item_list if \
                str(item[SC.K_TTVT_2]).lower() == ttvt.lower()]
        )

        thgian_cb_phut = 0
        for item in bc_chi_tiet_mll_x_item_list:
            if str(item[SC.K_TTVT_2]).lower() == ttvt.lower():
                try:
                    thgian_cb_phut += int(item[SC.K_UI_TG_CBAO1])
                except ValueError as e:
                    LoggerUtil.get_logger().error(
                        f'BcCbaoMllService _count_info_of_ttvt_x_clr error {e}')

        return tong_so_bts, sco_mll_lan, thgian_cb_phut

    def _count_info_of_ttvt_x_nclr(
                            self,
                            ttvt: str
    ):
        tong_so_bts = 0
        for item in self._bts_xg_onair_items_list:
            try:
                if str(self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                        [item[SC.K_MA_CSHT]][SC.K_TEN_TTVT_TRAM_VT_NETX]).lower() == \
                        ttvt.lower():
                    tong_so_bts += 1
            except KeyError as e:
                LoggerUtil.get_logger().warning(
                    f'BcCbaoMllService _count_info_of_ttvt_x_nclr: tong_so_bts failed {e}')

        mll_3g = 0
        mll_4g = 0
        mll_5g = 0
        for item in self._data_bc_cbao_mll_bts_xg_nclr_list:
            if str(item[SC.K_TTVT_2]).lower() == ttvt.lower():
                match item[SC.K_UI_HE_THONG1]:
                    case T.HeThong._3G.value:
                        mll_3g += 1
                    case T.HeThong._4G.value:
                        mll_4g += 1
                    case T.HeThong._5G.value:
                        mll_5g += 1

        tong_mll = mll_3g + mll_4g + mll_5g

        tg_csht_macro = 0
        for item in self._csht_ccl_service.csht_mdsd_items_list_all:
            if str(item[SC.K_TEN_TTVT_TRAM_VT_NETX]).lower() != ttvt.lower():
                continue

            if str(item[SC.K_MA_LOAI_CSHT_DDONG]).lower() == 'macro':
                tg_csht_macro += 1

        csht_macro_mll = 0
        for item in self._data_bc_csht_mll_nclr_list:
            if str(item[SC.K_TTVT_2]).lower() != ttvt.lower():
                continue

            if str(item[SC.K_UI_MA_LOAI_CSHT_DI_DONG]).lower() == 'macro':
                csht_macro_mll += 1

        return tong_so_bts, mll_3g, mll_4g, mll_5g, tong_mll, \
            tg_csht_macro, csht_macro_mll

    def _make_data_bc_chi_tiet_mll_xg_item_clr(self, rp_al_item_dict: dict) -> None|dict:
        item = {}
        item[SC.K_STT] = 0
        item[SC.K_NE] = rp_al_item_dict[SC.K_TEN_NE]
        item[SC.K_UI_TG_SU_CO2] = rp_al_item_dict[SC.K_TG_SU_CO_1]
        item[SC.K_UI_TG_CLR1] = rp_al_item_dict[SC.K_TG_CLR]
        item[SC.K_UI_TG_CBAO1] = to_int(rp_al_item_dict[SC.K_TG_CBAO], force=False)
        item[SC.K_UI_VNP_GHI_CHU1] = rp_al_item_dict[SC.K_VNP_GHI_CHU]
        item[SC.K_UI_TINH_GHI_CHU1] = rp_al_item_dict[SC.K_TINH_GHI_CHU]
        item[SC.K_UI_LOAI_SU_CO1] = to_int(rp_al_item_dict[SC.K_LOAI_SU_CO], force=False)
        item[SC.K_UI_TG_CBAO_AC] = rp_al_item_dict[SC.K_TIME_AC]
        item[SC.K_UI_PHAN_LOAI_TRAM] = rp_al_item_dict[SC.K_PHAN_LOAI_TRAM]

        #
        if item[SC.K_UI_PHAN_LOAI_TRAM] in ["", None]:
            item[SC.K_UI_PHAN_LOAI_TRAM] = "FMS chưa có phân loại trạm"

            msg = f'FMS chưa có phân loại trạm'
            if self._ui_set_error_callback: self._ui_set_error_callback(
                item.get(SC.K_NE), msg
            )
            LoggerUtil.get_logger().warning(
                f"{self.__class__.__name__} {item.get(SC.K_NE)} {msg}"
            )

        try:
            item[SC.K_UI_TEN_TRAM] = self._bts_all_items_ten_tren_hthong_dict\
                [(rp_al_item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT], rp_al_item_dict[SC.K_HE_THONG])]\
                [SC.K_TEN_QUAN_LY]
            item[SC.K_CSHT] = self._bts_all_items_ten_tren_hthong_dict\
                [(rp_al_item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT], rp_al_item_dict[SC.K_HE_THONG])]\
                [SC.K_MA_CSHT]
            # item[SC.K_UI_TRTHAI_DAT_MNO] = self._bts_all_items_ten_tren_hthong_dict\
            #     [(rp_al_item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT], rp_al_item_dict[SC.K_HE_THONG])]\
            #     [SC.K_TRTHAI_DAT_MNO] #234G
        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_NE}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed bts_all {item[SC.K_NE]} : {msg} : {e}')
            return None

        if str(item[SC.K_CSHT]) == "":
            msg = f'{SC.K_UI_MSG_KGAN_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed csht {item[SC.K_NE]} : {msg}')
            item[SC.K_TTVT_2] = SC.K_UI_MSG_KGAN_CSHT
            item[SC.K_UI_TO_HA_TANG] = SC.K_UI_MSG_KGAN_CSHT
            # if rp_al_item_dict[SC.K_HE_THONG] == T.HeThong._5G.value:
            #     if item[SC.K_UI_TRTHAI_DAT_MNO] == SC.K_UI_MSG_MISS_DB:
            #         item[SC.K_UI_TRTHAI_DAT_MNO] = SC.K_UI_MSG_KGAN_CSHT #5G
            item[SC.K_UI_TRTHAI_DAT_MNO] = SC.K_UI_MSG_KGAN_CSHT
            item[SC.K_UI_NVIEN_HTANG] = SC.K_UI_MSG_KGAN_CSHT

            return item

        try:
            item[SC.K_TTVT_2] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[item[SC.K_CSHT]][SC.K_TEN_TTVT_TRAM_VT_NETX]
            item[SC.K_UI_TO_HA_TANG] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[item[SC.K_CSHT]][SC.K_TEN_DVI_QLY]
            # if rp_al_item_dict[SC.K_HE_THONG] == T.HeThong._5G.value:
            #     if item[SC.K_UI_TRTHAI_DAT_MNO] == SC.K_UI_MSG_MISS_DB:
            #         item[SC.K_UI_TRTHAI_DAT_MNO] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
            #             [item[SC.K_CSHT]][SC.K_TRTHAI_DAT_MNO] #5G
            item[SC.K_UI_TRTHAI_DAT_MNO] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                [item[SC.K_CSHT]][SC.K_TRTHAI_DAT_MNO]

        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed csht ccl {item[SC.K_NE]} : {msg} : {e}')
            item[SC.K_TTVT_2] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_TO_HA_TANG]  = SC.K_UI_MSG_KTTHAY_CSHT
            # if rp_al_item_dict[SC.K_HE_THONG] == T.HeThong._5G.value:
            #     if item[SC.K_UI_TRTHAI_DAT_MNO] == SC.K_UI_MSG_MISS_DB:
            #         item[SC.K_UI_TRTHAI_DAT_MNO] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_TRTHAI_DAT_MNO] = SC.K_UI_MSG_KTTHAY_CSHT

        try:
            item[SC.K_UI_NVIEN_HTANG] = \
                self._dmoi_qly_csht_maker.dmoi_qly_csht_items_ma_csht_dict[item[SC.K_CSHT]][SC.K_HO_TEN]
        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_DAU_MOI_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed dmoi qly {item[SC.K_NE]} : {msg} : {e}')
            item[SC.K_UI_NVIEN_HTANG] = SC.K_UI_MSG_KTTHAY_DAU_MOI_CSHT

        #check to_ha_tang
        if item[SC.K_UI_TO_HA_TANG] == "" and rp_al_item_dict[SC.K_DVI_QLY] != "":
            msg = f'Tổ hạ tầng không khớp: CSHT vs Report AL'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr warning {item[SC.K_NE]} : {msg}'
            )
        else:
            if str(item[SC.K_UI_TO_HA_TANG]).lower() not in str(rp_al_item_dict[SC.K_DVI_QLY]).lower():
                msg = f'Tổ hạ tầng không khớp: CSHT vs Report AL'
                if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
                LoggerUtil.get_logger().warning(
                    f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr warning {item[SC.K_NE]} : {msg}'
                )

        return item

    #make BC chi tiết MLL_tất cả các NN XG / make BC MLL_nguồn(trừL3_KoMPĐ)-TD
    def _make_data_bc_chi_tiet_xg_clr(self):
        for item in self._rp_al_cbao_mll_maker.rp_alarm_items_list_bts_clr:
            _item_ret = self._make_data_bc_chi_tiet_mll_xg_item_clr(item)
            if _item_ret is None: continue

            he_thong = item[SC.K_HE_THONG]

            self._data_bc_cbao_mll_clr_xg_dict[he_thong].bc_chi_tiet_mll_tat_ca_nn_item_list.append(_item_ret)
            if self._is_item_of_bc_mll_nguon_td(_item_ret, he_thong):
                self._data_bc_cbao_mll_clr_xg_dict[he_thong].bc_mll_nguon_td_item_list.append(_item_ret)

        for he_thong in [T.HeThong._3G.value, T.HeThong._4G.value, T.HeThong._5G.value]:
            try:
                self._data_bc_cbao_mll_clr_xg_dict[he_thong].bc_chi_tiet_mll_tat_ca_nn_item_list = \
                    self._sort_data_bc_chi_tiet(
                        self._data_bc_cbao_mll_clr_xg_dict[he_thong].bc_chi_tiet_mll_tat_ca_nn_item_list
                    )
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'BcCbaoMllService _make_data_bc_chi_tiet_xg_clr failed sort bc_chi_tiet_mll_tat_ca_nn_item_list {he_thong} : {e}'
                )

            try:
                self._data_bc_cbao_mll_clr_xg_dict[he_thong].bc_mll_nguon_td_item_list = \
                    self._sort_data_bc_chi_tiet(
                        self._data_bc_cbao_mll_clr_xg_dict[he_thong].bc_mll_nguon_td_item_list
                    )
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'BcCbaoMllService _make_data_bc_chi_tiet_xg_clr failed sort bc_mll_nguon_td_item_list {he_thong} : {e}'
                )

    def _make_bc_tghop_item_clr(self, bts_xg_items_list_latest,
                            bc_chi_tiet_mll_x_item_list, ttvt_dict, compare_row: list):
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ttvt_dict[SC.K_TO_HA_TANG]

        item[SC.K_TTVT_2] = ttvt_dict[SC.K_TTVT]

        item[SC.K_UI_TONG_SO_BTS], item[SC.K_UI_SCO_MLL_LAN], item[SC.K_UI_TGIAN_CBAO_PHUT] = \
            self._count_info_of_ttvt_x_clr(
                bts_xg_items_list_latest, bc_chi_tiet_mll_x_item_list, item[SC.K_TTVT_2])

        if item[SC.K_UI_SCO_MLL_LAN] == 0:
            item[SC.K_UI_BINH_QUAN_PHUT_LAN] = round(0, 2)
        else:
            item[SC.K_UI_BINH_QUAN_PHUT_LAN] = \
                round(float(item[SC.K_UI_TGIAN_CBAO_PHUT]) / float(item[SC.K_UI_SCO_MLL_LAN]), 2)

        if item[SC.K_UI_TONG_SO_BTS] == 0:
            item[SC.K_UI_TY_LE_PHUT_BTS] = round(0, 2)
        else:
            item[SC.K_UI_TY_LE_PHUT_BTS] = \
                round(float(item[SC.K_UI_TGIAN_CBAO_PHUT]) / float(item[SC.K_UI_TONG_SO_BTS]), 2)

        #
        if isinstance(compare_row, list) and len(compare_row) == 1:
            item[SC.K_UI_TG_SO_BTS_TGGIAM_TRAM] = \
                int(item[SC.K_UI_TONG_SO_BTS]) - int(compare_row[0][SC.K_TONG_SO_BTS])

            item[SC.K_UI_SU_CO_MLL_TGGIAM_LAN] = \
                int(item[SC.K_UI_SCO_MLL_LAN]) - int(compare_row[0][SC.K_SCO_MLL_LAN])
            item[SC.K_UI_THGIAN_CBAO_TGGIAM_PHUT] = \
                int(item[SC.K_UI_TGIAN_CBAO_PHUT]) - int(compare_row[0][SC.K_TGIAN_CBAO_PHUT])
            item[SC.K_UI_BINH_QUAN_TGGIAM_PHUT_LAN] = \
                round(float(item[SC.K_UI_BINH_QUAN_PHUT_LAN]) - float(compare_row[0][SC.K_BINH_QUAN_PHUT_LAN]), 2)
            item[SC.K_UI_TY_LE_TGGIAM_PHUT_BTS] = \
                round(float(item[SC.K_UI_TY_LE_PHUT_BTS]) - float(compare_row[0][SC.K_TY_LE_PHUT_BTS]), 2)

        else:
            item[SC.K_UI_TG_SO_BTS_TGGIAM_TRAM] = SC.K_UI_MSG_MISS_DB
            item[SC.K_UI_SU_CO_MLL_TGGIAM_LAN] = SC.K_UI_MSG_MISS_DB
            item[SC.K_UI_THGIAN_CBAO_TGGIAM_PHUT] = SC.K_UI_MSG_MISS_DB
            item[SC.K_UI_BINH_QUAN_TGGIAM_PHUT_LAN] = SC.K_UI_MSG_MISS_DB
            item[SC.K_UI_TY_LE_TGGIAM_PHUT_BTS] = SC.K_UI_MSG_MISS_DB

        return item

    def _make_data_bc_tong_hop_xg_clr(self, he_thong):
        bang_tghop_mll_item_list = []
        bang_tghop_mll_da_loai_tru_item_list = []

        match he_thong:
            case T.HeThong._3G.value:
                bts_xg_items_list_latest = self._nodeb3g_sheet_maker.nodeb3g_items_list_all
                data_bc_cbao_mll_xg: DataBcCbaoMllXgStruct = self._data_bc_cbao_mll_clr_xg_dict[T.HeThong._3G.value]
            case T.HeThong._4G.value:
                bts_xg_items_list_latest = self._enodeb4g_sheet_maker.enodeb4g_items_list_all
                data_bc_cbao_mll_xg: DataBcCbaoMllXgStruct = self._data_bc_cbao_mll_clr_xg_dict[T.HeThong._4G.value]
            case T.HeThong._5G.value:
                bts_xg_items_list_latest = self._gnodeb5g_sheet_maker.gnodeb5g_items_list_all
                data_bc_cbao_mll_xg: DataBcCbaoMllXgStruct = self._data_bc_cbao_mll_clr_xg_dict[T.HeThong._5G.value]

        dynamicInfoUtil = DynamicInfoUtil()
        site: str = dynamicInfoUtil.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        rp_time_type = dynamicInfoUtil.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE)
        year_cpare = dynamicInfoUtil.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_YEAR_COMPARE)
        rp_time_compare = dynamicInfoUtil.get_value(
            2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE_BC_MLL
        )
        compare_row_dict = {
            SC.K_HE_THONG: he_thong,
            SC.K_NAM: year_cpare,
            SC.K_RP_TIME_TYPE: rp_time_type,
            SC.K_RP_TIME: rp_time_compare
        }

        # get time cpare
        db_row_cpare = dict(compare_row_dict)
        db_row_cpare: list = self._db_adapter.get_rows_list_by_value(
            SC.K_TABLE_BC_BTS_MLL_TGHOP, db_row_cpare
        )
        if len(db_row_cpare) > 0:
            rp_time_from_cp = db_row_cpare[0][SC.K_RP_TIME_FROM]
            rp_time_to_cp = db_row_cpare[0][SC.K_RP_TIME_TO]
        else:
            rp_time_from_cp = SC.K_UI_MSG_MISS_DB
            rp_time_to_cp = SC.K_UI_MSG_MISS_DB
        dynamicInfoUtil.set_value(
            rp_time_from_cp, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_FROM_CPARE)
        dynamicInfoUtil.set_value(
            rp_time_to_cp, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TO_CPARE)

        #
        for ttvt_dict in self._tht_ttvt_maker.ttvt_list:
            if site.lower() == ST.Site.ALL_SITE.value:
                pass
            elif site.lower() not in str(ttvt_dict[SC.K_SITE1]).lower():
                continue

            db_row_cpare = dict(compare_row_dict)
            db_row_cpare[SC.K_TTVT] = ttvt_dict[SC.K_TTVT]
            db_row_cpare: list = self._db_adapter.get_rows_list_by_value(
                SC.K_TABLE_BC_BTS_MLL_TGHOP, db_row_cpare)
            item = self._make_bc_tghop_item_clr(
                bts_xg_items_list_latest,
                data_bc_cbao_mll_xg.bc_chi_tiet_mll_tat_ca_nn_item_list,
                ttvt_dict, db_row_cpare
            )
            bang_tghop_mll_item_list.append(item)

            db_row_cpare = dict(compare_row_dict)
            db_row_cpare[SC.K_TTVT] = ttvt_dict[SC.K_TTVT]
            db_row_cpare: list = self._db_adapter.get_rows_list_by_value(
                SC.K_TABLE_BC_BTS_MLL_TGHOP_DA_LOAI_TRU, db_row_cpare)
            item = self._make_bc_tghop_item_clr(
                bts_xg_items_list_latest,
                data_bc_cbao_mll_xg.bc_mll_nguon_td_item_list,
                ttvt_dict, db_row_cpare
            )
            bang_tghop_mll_da_loai_tru_item_list.append(item)

        # sort Đơn vị quản lý -> TTVT
        try:
            bang_tghop_mll_item_list.sort(
                key=lambda x: (
                    safe_sort_value(locale.strxfrm(x[SC.K_UI_DON_VI_QUAN_LY])),
                    safe_sort_value(locale.strxfrm(x[SC.K_TTVT_2])),
                )
            )
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcCbaoMllService _make_data_bc_tong_hop_xg_clr failed sort bang_tghop_mll_item_list: {e}'
            )

        try:
            bang_tghop_mll_da_loai_tru_item_list.sort(
                key=lambda x: (
                    safe_sort_value(locale.strxfrm(x[SC.K_UI_DON_VI_QUAN_LY])),
                    safe_sort_value(locale.strxfrm(x[SC.K_TTVT_2])),
                )
            )
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcCbaoMllService _make_data_bc_tong_hop_xg_clr failed sort bang_tghop_mll_da_loai_tru_item_list: {e}'
            )

        return bang_tghop_mll_item_list, bang_tghop_mll_da_loai_tru_item_list

    def _make_data_bc_tong_hop_clr(self):
        for he_thong in [T.HeThong._3G.value, T.HeThong._4G.value, T.HeThong._5G.value]:
            self._data_bc_cbao_mll_clr_xg_dict[he_thong].bc_tghop_bang_tghop_mll_item_list, \
            self._data_bc_cbao_mll_clr_xg_dict[he_thong].bc_tghop_bang_tghop_mll_da_loai_tru_item_list = \
                self._make_data_bc_tong_hop_xg_clr(he_thong)

    ######################################################################## NCLR

    def _make_data_bc_chi_tiet_item_nclr(self, rp_al_item_dict): #MLL BTS TTVT X & CANHBAO_MATAC
        item = {}
        item[SC.K_STT] = 0
        item[SC.K_NE] = rp_al_item_dict[SC.K_TEN_NE]
        item[SC.K_UI_HE_THONG1] = rp_al_item_dict[SC.K_HE_THONG]
        item[SC.K_UI_TG_SU_CO2] = rp_al_item_dict[SC.K_TG_SU_CO_1]
        item[SC.K_UI_VNP_GHI_CHU1] = rp_al_item_dict[SC.K_VNP_GHI_CHU]
        item[SC.K_UI_TINH_GHI_CHU1] = rp_al_item_dict[SC.K_TINH_GHI_CHU]
        item[SC.K_UI_PHAN_LOAI_TRAM] = rp_al_item_dict[SC.K_PHAN_LOAI_TRAM]

        #
        if item[SC.K_UI_PHAN_LOAI_TRAM] in ["", None]:
            item[SC.K_UI_PHAN_LOAI_TRAM] = "FMS chưa có phân loại trạm"

            msg = f'FMS chưa có phân loại trạm'
            if self._ui_set_error_callback: self._ui_set_error_callback(
                item.get(SC.K_NE), msg
            )
            LoggerUtil.get_logger().warning(
                f"{self.__class__.__name__} {item.get(SC.K_NE)} {msg}"
            )

        try:
            item[SC.K_UI_TEN_TRAM] = self._bts_all_items_ten_tren_hthong_dict\
                [(rp_al_item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT], rp_al_item_dict[SC.K_HE_THONG])]\
                [SC.K_TEN_QUAN_LY]
            item[SC.K_CSHT] = self._bts_all_items_ten_tren_hthong_dict\
                [(rp_al_item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT], rp_al_item_dict[SC.K_HE_THONG])]\
                [SC.K_MA_CSHT]
            # item[SC.K_UI_TRTHAI_DAT_MNO] = self._bts_all_items_ten_tren_hthong_dict\
            #     [(rp_al_item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT], rp_al_item_dict[SC.K_HE_THONG])]\
            #     [SC.K_TRTHAI_DAT_MNO] #234G
        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_NE}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed bts_all {item[SC.K_NE]} : {msg} : {e}')
            return None

        if str(item[SC.K_CSHT]) == "":
            msg = f'{SC.K_UI_MSG_KGAN_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed csht {item[SC.K_NE]} : {msg}')
            item[SC.K_TTVT_2] = SC.K_UI_MSG_MISS_DB
            item[SC.K_UI_TO_HA_TANG] = SC.K_UI_MSG_MISS_DB
            item[SC.K_UI_NVIEN_HTANG] = SC.K_UI_MSG_MISS_DB
            return item

        try:
            item[SC.K_TTVT_2] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[item[SC.K_CSHT]][SC.K_TEN_TTVT_TRAM_VT_NETX]
            item[SC.K_UI_TO_HA_TANG] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[item[SC.K_CSHT]][SC.K_TEN_DVI_QLY]
            # if rp_al_item_dict[SC.K_HE_THONG] == T.HeThong._5G.value:
            #     if item[SC.K_UI_TRTHAI_DAT_MNO] == SC.K_UI_MSG_MISS_DB:
            #         item[SC.K_UI_TRTHAI_DAT_MNO] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
            #             [item[SC.K_CSHT]][SC.K_TRTHAI_DAT_MNO] #5G
            item[SC.K_UI_TRTHAI_DAT_MNO] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                [item[SC.K_CSHT]][SC.K_TRTHAI_DAT_MNO]

        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed csht ccl {item[SC.K_NE]} : {msg} : {e}')
            item[SC.K_TTVT_2] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_TO_HA_TANG] = SC.K_UI_MSG_KTTHAY_CSHT
            # if rp_al_item_dict[SC.K_HE_THONG] == T.HeThong._5G.value:
            #     if item[SC.K_UI_TRTHAI_DAT_MNO] == SC.K_UI_MSG_MISS_DB:
            #         item[SC.K_UI_TRTHAI_DAT_MNO] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_TRTHAI_DAT_MNO] = SC.K_UI_MSG_KTTHAY_CSHT

        try:
            item[SC.K_UI_NVIEN_HTANG] = \
                self._dmoi_qly_csht_maker.dmoi_qly_csht_items_ma_csht_dict[item[SC.K_CSHT]][SC.K_HO_TEN]
        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_DAU_MOI_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed dmoi qly {item[SC.K_NE]} : {msg} : {e}')
            item[SC.K_UI_NVIEN_HTANG] = SC.K_UI_MSG_KTTHAY_DAU_MOI_CSHT

        return item

    def _make_data_bc_mll_bts_ttvtx_nclr(self):
        for item in self._rp_al_cbao_mll_maker.rp_alarm_items_list_bts_nclr:
            _item_ret = self._make_data_bc_chi_tiet_item_nclr(item)
            if _item_ret is None: continue

            self._data_bc_cbao_mll_bts_xg_nclr_list.append(_item_ret)

        try:
            self._data_bc_cbao_mll_bts_xg_nclr_list = \
                self._sort_data_bc_chi_tiet(self._data_bc_cbao_mll_bts_xg_nclr_list)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcCbaoMllService _make_data_bc_mll_bts_ttvtx_nclr failed sort data_bc_cbao_mll_bts_xg_nclr_list: {e}'
            )

    def _make_data_bc_mat_nguon_ac_nclr(self):
        for item in self._rp_al_cbao_mll_maker.rp_al_item_list_nguon_ac_nclr:
            _item_ret = self._make_data_bc_chi_tiet_item_nclr(item)
            if _item_ret is None: continue

            self._data_bc_mat_nguon_ac_nclr_list.append(_item_ret)

        try:
            self._data_bc_mat_nguon_ac_nclr_list = \
                self._sort_data_bc_chi_tiet(self._data_bc_mat_nguon_ac_nclr_list)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcCbaoMllService _make_data_bc_mat_nguon_ac_nclr failed sort data_bc_mat_nguon_ac_nclr_list: {e}'
            )

    def _make_data_bc_csht_mll_nclr_item(self, rp_al_item_list):
        if rp_al_item_list == None or len(rp_al_item_list) == 0: return None

        def get_one_from_list():
            for item in rp_al_item_list:
                if "nguồn" in str(item[SC.K_NGUYEN_NHAN]).lower():
                    return item
            for item in rp_al_item_list:
                if item[SC.K_HE_THONG] in [T.HeThong._3G.value, T.HeThong._4G.value]:
                    return item
            return rp_al_item_list[0]

        rp_al_item_dict: dict = get_one_from_list()

        item = {}
        item[SC.K_STT] = 0 #"STT"
        item[SC.K_UI_NGUYEN_NHAN1] = rp_al_item_dict[SC.K_NGUYEN_NHAN]
        item[SC.K_UI_TG_SU_CO2] = rp_al_item_dict[SC.K_TG_SU_CO_1]
        item[SC.K_UI_PHAN_LOAI_TRAM] = rp_al_item_dict[SC.K_PHAN_LOAI_TRAM]
        item[SC.K_UI_MA_TRAM] = self._extract_ma_tram_from_ten_ne(rp_al_item_dict[SC.K_TEN_NE])

        if item[SC.K_UI_PHAN_LOAI_TRAM] in ["", None]:
            item[SC.K_UI_PHAN_LOAI_TRAM] = "FMS chưa có phân loại trạm"

            msg = f'FMS chưa có phân loại trạm'
            if self._ui_set_error_callback: self._ui_set_error_callback(
                rp_al_item_dict.get(SC.K_TEN_NE), msg
            )
            LoggerUtil.get_logger().warning(
                f"{self.__class__.__name__} {rp_al_item_dict.get(SC.K_TEN_NE)} {msg}"
            )

        try:
            item[SC.K_UI_MA_CSHT] = self._bts_all_items_ten_tren_hthong_dict\
                [rp_al_item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT]][SC.K_MA_CSHT]
            # item[SC.K_UI_TRTHAI_DAT_MNO] = self._bts_all_items_ten_tren_hthong_dict\
            #     [rp_al_item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT]][SC.K_TRTHAI_DAT_MNO] #234G
        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_NE}'
            if self._ui_set_error_callback: self._ui_set_error_callback(
                rp_al_item_dict[SC.K_TEN_NE], msg
            )
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_csht_mll_nclr_item failed bts_all'
                f' {rp_al_item_dict[SC.K_TEN_NE]} : {msg} : {e}')
            return None

        try:
            item[SC.K_UI_TEN_CSHT] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[item[SC.K_UI_MA_CSHT]][SC.K_TEN_CSHT]
            item[SC.K_TTVT_2] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[item[SC.K_UI_MA_CSHT]][SC.K_TEN_TTVT_TRAM_VT_NETX]
            item[SC.K_UI_TO_HA_TANG] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[item[SC.K_UI_MA_CSHT]][SC.K_TEN_DVI_QLY]
            item[SC.K_UI_DIA_CHI] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                [item[SC.K_UI_MA_CSHT]][SC.K_DIA_CHI]
            item[SC.K_UI_PHUONG_XA] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                [item[SC.K_UI_MA_CSHT]][SC.K_PHUONG_XA]
            # if rp_al_item_dict[SC.K_HE_THONG] == T.HeThong._5G.value:
            #     if item[SC.K_UI_TRTHAI_DAT_MNO] == SC.K_UI_MSG_MISS_DB:
            #         item[SC.K_UI_TRTHAI_DAT_MNO] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
            #             [item[SC.K_UI_MA_CSHT]][SC.K_TRTHAI_DAT_MNO] #5G
            item[SC.K_UI_TRTHAI_DAT_MNO] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                [item[SC.K_UI_MA_CSHT]][SC.K_TRTHAI_DAT_MNO]
            item[SC.K_UI_MA_LOAI_CSHT_DI_DONG] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                [item[SC.K_UI_MA_CSHT]][SC.K_MA_LOAI_CSHT_DDONG]

        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(
                rp_al_item_dict[SC.K_TEN_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_csht_mll_nclr_item failed csht ccl'
                f'{rp_al_item_dict[SC.K_TEN_NE]} : {msg} : {e}')
            item[SC.K_UI_TEN_CSHT] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_TTVT_2] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_TO_HA_TANG] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_DIA_CHI] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_PHUONG_XA] = SC.K_UI_MSG_KTTHAY_CSHT
            # if rp_al_item_dict[SC.K_HE_THONG] == T.HeThong._5G.value:
            #     if item[SC.K_UI_TRTHAI_DAT_MNO] == SC.K_UI_MSG_MISS_DB:
            #         item[SC.K_UI_TRTHAI_DAT_MNO] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_TRTHAI_DAT_MNO] = SC.K_UI_MSG_KTTHAY_CSHT

        try:
            item[SC.K_UI_NVIEN_HTANG] = \
                self._dmoi_qly_csht_maker.dmoi_qly_csht_items_ma_csht_dict[item[SC.K_UI_MA_CSHT]][SC.K_HO_TEN]
        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_DAU_MOI_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(
                rp_al_item_dict[SC.K_TEN_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_csht_mll_nclr_item failed dmoi qly'
                f'{rp_al_item_dict[SC.K_TEN_NE]} : {msg} : {e}'
            )
            item[SC.K_UI_NVIEN_HTANG] = SC.K_UI_MSG_KTTHAY_DAU_MOI_CSHT

        return item

    def _make_data_bc_csht_mll_nclr(self):
        if len(self._rp_al_cbao_mll_maker.rp_alarm_items_list_bts_nclr) == 0: #chỉ lấy 5 NN BTS
            LoggerUtil.get_logger().info(
                f'BcCbaoMllService _make_data_bc_csht_mll_nclr empty'
            )
            return

        rp_al_bts_mll_ma_tram_dict = defaultdict(list)
        for item in self._rp_al_cbao_mll_maker.rp_alarm_items_list_bts_nclr:
            ma_tram = self._extract_ma_tram_from_ten_ne(item[SC.K_TEN_NE])
            rp_al_bts_mll_ma_tram_dict[ma_tram].append(item)

        #
        for ma_tram, rp_al_item_list in rp_al_bts_mll_ma_tram_dict.items():
            ne_mll_set = set([item[SC.K_TEN_TREN_HE_THONG_COMPACT] for item in rp_al_item_list])

            item_all_list = self._bts_xg_ma_tram_dict.get(ma_tram, [])
            ne_all_set = set(
                [item[SC.K_TEN_TREN_HE_THONG_COMPACT] for item in item_all_list]
            )

            if (ne_all_set == ne_mll_set) or (ne_all_set.issubset(ne_mll_set)):
                ret = self._make_data_bc_csht_mll_nclr_item(rp_al_item_list)
                if ret != None:
                    self._data_bc_csht_mll_nclr_list.append(ret)

        try:
            self._data_bc_csht_mll_nclr_list = \
                self._sort_data_bc_chi_tiet(self._data_bc_csht_mll_nclr_list)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcCbaoMllService _make_data_bc_csht_mll_nclr failed sort data_bc_csht_mll_nclr_list: {e}'
            )

    def _make_bc_tghop_item_nclr(self, ttvt_dict):
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ttvt_dict[SC.K_TO_HA_TANG] #

        item[SC.K_TTVT_2] = ttvt_dict[SC.K_TTVT] #2

        # Tổng số BTS, 3G MLL, 4G MLL, 5G MLL, Tổng MLL, Tổng CSHT Macro, CSHT macro MLL
        item[3], item[4], item[5], item[6], item[7], item[8], item[9] \
            = self._count_info_of_ttvt_x_nclr(ttvt_dict[SC.K_TTVT])

        row_cpare = self._bc_nclr_maker.bc_tghop_ttvt_dict.get(ttvt_dict[SC.K_TTVT], {})
        if self._need_cpare_nclr == "1":
            if len(row_cpare) > 0:
                item[10] = item[3] - row_cpare[SC.K_TONG_SO_BTS] #Tổng số BTS
                item[11] = item[4] - row_cpare[SC.K_3G_MLL] #3G MLL
                item[12] = item[5] - row_cpare[SC.K_4G_MLL] #4G MLL
                item[13] = item[6] - row_cpare[SC.K_5G_MLL] #5G MLL
                item[14] = item[7] - row_cpare[SC.K_TONG_MLL] #Tổng MLL
                item[15] = item[8] - row_cpare[SC.K_TONG_CSHT_MACRO] #Tổng CSHT Macro
                item[16] = item[9] - row_cpare[SC.K_CSHT_MACRO_MLL] #CSHT macro MLL
            else:
                for i in range(10, 17):
                    item[i] = SC.K_UI_MSG_MISS_DB

        return item

    def _make_data_bc_tong_hop_nclr(self):
        site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

        for ttvt_dict in self._tht_ttvt_maker.ttvt_list:
            if site.lower() == ST.Site.ALL_SITE.value:
                pass
            elif site.lower() not in str(ttvt_dict[SC.K_SITE1]).lower():
                continue

            ret = self._make_bc_tghop_item_nclr(
                ttvt_dict
            )
            if ret != None:
                self._data_bc_tghop_nclr_list.append(ret)

        self._data_bc_tghop_nclr_list.sort(
            key=lambda x: (
                safe_sort_value(locale.strxfrm(x[SC.K_UI_DON_VI_QUAN_LY])),
                safe_sort_value(locale.strxfrm(x[SC.K_TTVT_2])),
            )
        )

        for item in self._data_bc_tghop_nclr_list:
            item[1] = item.pop(SC.K_UI_DON_VI_QUAN_LY)
            item[2] = item.pop(SC.K_TTVT_2)

        # row tổng cộng
        item = {}
        item[1] = ""
        item[2] = "Tổng"
        item[3] = sum(#Tổng số BTS
            [item[3] for item in self._data_bc_tghop_nclr_list]
        )
        item[4] = sum(# 3G
            [item[4] for item in self._data_bc_tghop_nclr_list]
        )
        item[5] = sum(# 4G
            [item[5] for item in self._data_bc_tghop_nclr_list]
        )
        item[6] = sum(# 5G
            [item[6] for item in self._data_bc_tghop_nclr_list]
        )
        item[7] = sum(# Tổng MLL
            [item[7] for item in self._data_bc_tghop_nclr_list]
        )
        item[8] = sum(# Tổng CSHT Macro
            [item[8] for item in self._data_bc_tghop_nclr_list]
        )
        item[9] = sum(# CSHT Macro MLL
            [item[9] for item in self._data_bc_tghop_nclr_list]
        )
        row_cpare = self._bc_nclr_maker.bc_tghop_ttvt_dict.get(item[2], {})
        if self._need_cpare_nclr == "1":
            if len(row_cpare) > 0:
                item[10] = item[3] - row_cpare[SC.K_TONG_SO_BTS] #Tổng số BTS
                item[11] = item[4] - row_cpare[SC.K_3G_MLL] #3G MLL
                item[12] = item[5] - row_cpare[SC.K_4G_MLL] #4G MLL
                item[13] = item[6] - row_cpare[SC.K_5G_MLL] #5G MLL
                item[14] = item[7] - row_cpare[SC.K_TONG_MLL] #Tổng MLL
                item[15] = item[8] - row_cpare[SC.K_TONG_CSHT_MACRO] #Tổng CSHT Macro
                item[16] = item[9] - row_cpare[SC.K_CSHT_MACRO_MLL] #CSHT macro MLL
            else:
                for i in range(10, 17):
                    item[i] = SC.K_UI_MSG_MISS_DB

        self._data_bc_tghop_nclr_list.insert(0, item)

    def make_bc(self):
        ret_path = None

        # init data
        self._init_data()
        # prepare data
        self._prepare_data()

        writer = ExcelBcCbaoMllWriter()

        ################################# _make_bc_cbao_mll_clr
        # make data BC chi tiết MLL_tất cả các NN XG & make BC MLL_nguồn(trừL3_KoMPĐ)-TD
        self._make_data_bc_chi_tiet_xg_clr()
        # make data BÁO CÁO TỔNG HỢP
        self._make_data_bc_tong_hop_clr()

        need_save_to_db = DynamicInfoUtil().get_value(
            2, SC.K_SCREEN_INPUT, SC.K_SAVE_BC_THOP_TO_DB)
        if (need_save_to_db != "0") and (Session.get_role() == "admin"):
            writer.write_db(
                self._data_bc_cbao_mll_clr_xg_dict
            )

        ret_path = writer.write_excel_clr(
            self._data_bc_cbao_mll_clr_xg_dict
        )

        ############################### _make_bc_cbao_mll_nclr
        # make data BC MLL TTVT X
        self._make_data_bc_mll_bts_ttvtx_nclr()
        # make data CANHBAO_MATAC
        self._make_data_bc_mat_nguon_ac_nclr()
        # make data CSHT Mất liên lạc
        self._make_data_bc_csht_mll_nclr()
        # make data BÁO CÁO TỔNG HỢP
        self._make_data_bc_tong_hop_nclr()

        writer.write_excel_nclr(
            self._data_bc_cbao_mll_bts_xg_nclr_list,
            self._data_bc_mat_nguon_ac_nclr_list,
            self._data_bc_csht_mll_nclr_list,
            self._data_bc_tghop_nclr_list
        )

        return ret_path
class ExcelDsachLoiWriter:
    def __init__(self):
        pass

    def write_excel(self, data: list) -> str:
        return self._write_excel_dsach_loi(data)

    def _write_data_to_excel_by_header(self, sheet_opened: Worksheet, row_index, header_dict, data_dict):
        for header in header_dict.keys():
            sheet_opened.cell(row=row_index, column=header_dict[header]).value = data_dict[header]
            T.format_normal_cell(sheet_opened.cell(row=row_index, column=header_dict[header]))

    def _create_dsach_loi_output(self) -> str:
        dynamic_info_util = DynamicInfoUtil()
        explorer_util = ExplorerUtil()

        output_folder_path = (
            dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_OUTPUT_PATH)
            or self._output_folder_path
        )
        excel_dsach_loi_name = (
            SC.K_EXCEL_DSACH_LOI_TEMPLATE.replace("template.xlsx", "")
            + str(dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_REPORT_TYPE) or "")
            + ".xlsx"
        )

        excel_dsach_loi_path = os.path.join(
            output_folder_path, excel_dsach_loi_name
        )

        excel_output_template_path = (
            explorer_util.get_output_template_file_path(SC.K_EXCEL_DSACH_LOI_TEMPLATE)
        )

        shutil.copy(excel_output_template_path, excel_dsach_loi_path)
        return excel_dsach_loi_path

    def _write_excel_dsach_loi(self, data: list) -> str:
        excel_path = self._create_dsach_loi_output()

        wb = openpyxl.load_workbook(excel_path)
        sheet = wb[SC.K_SHEET_DSACH_LOI]
        header_dict = {
            SC.K_UI_ERROR: 2,
            SC.K_UI_DESCRIPTION: 3,
        }
        start_row = 2
        for item in data:
            start_row += 1
            self._write_data_to_excel_by_header(sheet, start_row, header_dict, item)

        wb.save(excel_path)
        wb.close()

        return excel_path