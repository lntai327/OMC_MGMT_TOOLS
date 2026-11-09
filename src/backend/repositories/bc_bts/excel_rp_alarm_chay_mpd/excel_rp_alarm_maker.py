from backend.constant import type as T
from backend.repositories.bc_bts.excel_rp_alarm_chay_mpd.excel_rp_alarm_loader import *
from backend.repositories.bc_bts.excel_enodeb4g.excel_enodeb4g_maker import ExcelEnodeb4gSheetMaker
from backend.repositories.bc_bts.excel_gnodeb5g.excel_gnodeb5g_maker import ExcelGnodeb5gSheetMaker
from backend.repositories.bc_bts.excel_nodeb3g.excel_nodeb3g_maker import ExcelNodeb3gSheetMaker
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.repositories.common_csht_ccl_repo import CshtCclService

from share.util.logger_util import LoggerUtil
from share.constant import constant as SC
from share.constant import type as ST

class ExcelRpAlarmMaker():
    def __init__(self, ui_set_error_callback=None):
        self._ui_set_error_callback = ui_set_error_callback

        self._nodeb3g_sheet_maker = ExcelNodeb3gSheetMaker()
        self._enodeb4g_sheet_maker = ExcelEnodeb4gSheetMaker()
        self._gnodeb5g_sheet_maker = ExcelGnodeb5gSheetMaker()
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
                    f'ExcelRpAlarmMaker _normalize  : {item[SC.K_TEN_NE]}'
                    f' {SC.K_UI_MSG_NOT_DETECT_SITE}'
                )
                if self._ui_set_error_callback is not None:
                    self._ui_set_error_callback(
                        item[SC.K_TEN_NE], SC.K_UI_MSG_NOT_DETECT_SITE)
                self.rp_alarm_items_list_all.remove(item)
                continue