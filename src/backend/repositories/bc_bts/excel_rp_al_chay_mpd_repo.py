from backend.constant import type as T
from backend.repositories.bc_bts.excel_enodeb4g_repo import ExcelEnodeb4gService
from backend.repositories.bc_bts.excel_gnodeb5g_repo import ExcelGnodeb5gService
from backend.repositories.bc_bts.excel_nodeb3g_repo import ExcelNodeb3gService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.util.ex_handle_util import ExcelHandleUtil

from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil
from share.constant import constant as SC
from share.constant import type as ST

class DataSheet:
    def __init__(self):
        self._ten_ne = None
        self._tgian_su_co = None
        self._tgian_clr = None
        self._tgain_cbao: str = None
        self._vnp_ghi_chu = None
        self._tinh_ghi_chu = None
        self._loai_su_co = None
        self._time_ac = None
        self._phan_loai_tram = None
        self._he_thong = None
        self._dvi_qly = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TEN_NE: self._ten_ne,
            SC.K_TG_SU_CO_1: self._tgian_su_co,
            SC.K_TG_CLR: self._tgian_clr,
            SC.K_TG_CBAO: self._tgain_cbao,
            SC.K_VNP_GHI_CHU: self._vnp_ghi_chu,
            SC.K_TINH_GHI_CHU: self._tinh_ghi_chu,
            SC.K_LOAI_SU_CO: self._loai_su_co,
            SC.K_TIME_AC: self._time_ac,
            SC.K_PHAN_LOAI_TRAM: self._phan_loai_tram,
            SC.K_TTHAI_CLR: self._tthai_clr,
            SC.K_HE_THONG: self._he_thong,
            SC.K_DVI_QLY: self._dvi_qly,
        }

    def load(self, item_dic):
        self._ten_ne = item_dic.get(SC.K_UI_TEN_NE)
        self._tgian_su_co = item_dic.get(SC.K_UI_TG_SU_CO1)
        self._tgian_clr = item_dic.get(SC.K_UI_TG_CLR)
        self._tgain_cbao = item_dic.get(SC.K_UI_TG_CBAO)
        self._vnp_ghi_chu = item_dic.get(SC.K_UI_VNP_GHI_CHU)
        self._tinh_ghi_chu = item_dic.get(SC.K_UI_TINH_GHI_CHU)
        self._loai_su_co = item_dic.get(SC.K_UI_LOAI_SU_CO)
        self._time_ac = item_dic.get(SC.K_UI_TIME_AC)
        self._phan_loai_tram = item_dic.get(SC.K_UI_PHAN_LOAI_TRAM1)
        self._tthai_clr = item_dic.get(SC.K_UI_TTHAI_CLR)
        self._he_thong = item_dic.get(SC.K_UI_HE_THONG)
        self._dvi_qly = item_dic.get(SC.K_UI_DON_VI_QUAN_LY)
        return self

class ExcelRpAlarmLoader:
    def __init__(self):
        pass

    def load_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_RP_ALARM_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_DATA, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_DATA,
                excel_info_key=SC.K_EXCEL_RP_AL_BC_CHAY_MPD_QUA_BGS_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [DataSheet().load(x) for x in all_items_in_sheet_list]

class ExcelRpAlMpdService():
    def __init__(self, ui_set_error_callback=None):
        self._ui_set_error_callback = ui_set_error_callback

        self._nodeb3g_sheet_maker = ExcelNodeb3gService()
        self._enodeb4g_sheet_maker = ExcelEnodeb4gService()
        self._gnodeb5g_sheet_maker = ExcelGnodeb5gService()
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._csht_ccl_service = CshtCclService()

        self._rp_alarm_items_list_all_raw = []
        self.rp_alarm_items_list_all = []

    def load(self):
        self._loadFromExcel()
        self._tht_ttvt_maker.load()
        self._nodeb3g_sheet_maker.load()
        self._enodeb4g_sheet_maker.load()
        self._gnodeb5g_sheet_maker.load()
        self._csht_ccl_service.load()

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

        self._normalize()

    def _loadFromExcel(self):
        # load items
        items_list_all_raw = ExcelRpAlarmLoader().load_items()
        self._rp_alarm_items_list_all_raw = [item.to_dict() for item in items_list_all_raw]

    def _normalize(self):
        self.rp_alarm_items_list_all = self._rp_alarm_items_list_all_raw
        # Fillter condition
        site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

        for item in self.rp_alarm_items_list_all:
            ten_hthong = str(item[SC.K_TEN_NE])
            item[SC.K_TEN_TREN_HE_THONG_COMPACT] = (
                ten_hthong[2:].replace("-", "")
                if ten_hthong
                else ""
            )

        if site.lower() == ST.Site.ALL_SITE.value:
            return

        for item in self.rp_alarm_items_list_all[:]:
            try:
                ma_csht = self._bts_all_items_ten_tren_hthong_dict\
                    [(item[SC.K_TEN_TREN_HE_THONG_COMPACT], item[SC.K_HE_THONG])]\
                    [SC.K_MA_CSHT]
                tht = str(self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[ma_csht]\
                    [SC.K_TEN_DVI_QLY]).lower()
                if str(self._tht_ttvt_maker.tht_dict[tht][SC.K_SITE1]).lower() != \
                        str(site).lower():
                    self.rp_alarm_items_list_all.remove(item)
                    continue
                if str(item[SC.K_TG_CBAO]) == "0": #loai tru CLR, TG CB = 0; NCLR khong co TG CB
                    self.rp_alarm_items_list_all.remove(item)
                    continue
            except Exception as e:
                LoggerUtil.get_logger().warning(
                    f'ExcelRpAlMpdService _normalize  : {item[SC.K_TEN_NE]}'
                    f' {SC.K_UI_MSG_NOT_DETECT_SITE}'
                )
                if self._ui_set_error_callback is not None:
                    self._ui_set_error_callback(
                        item[SC.K_TEN_NE], SC.K_UI_MSG_NOT_DETECT_SITE)
                self.rp_alarm_items_list_all.remove(item)
                continue