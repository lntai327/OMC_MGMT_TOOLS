# from collections import defaultdict
from dateutil import parser
import locale

from backend.constant import type as T
from backend.repositories.bc_bts.excel_enodeb4g.excel_enodeb4g_maker import ExcelEnodeb4gSheetMaker
from backend.repositories.bc_bts.excel_gnodeb5g.excel_gnodeb5g_maker import ExcelGnodeb5gSheetMaker
from backend.repositories.bc_bts.excel_nodeb3g.excel_nodeb3g_maker import ExcelNodeb3gSheetMaker
from backend.repositories.bc_bts.excel_rp_alarm_cbao_mll.excel_rp_alarm_loader import ExcelRpAlarmLoader
from backend.repositories.bc_bts.cf_bts.cf_bts_maker import CFBtsMaker
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil

from share.constant import constant as SC
from share.constant import type as ST

class ExcelRpAlarmCbaoMllMaker():
    def __init__(self, ui_set_error_callback=None):
        locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')
        
        self._ui_set_error_callback = ui_set_error_callback
        self._init_data()

        self._nodeb3g_sheet_maker = ExcelNodeb3gSheetMaker()
        self._enodeb4g_sheet_maker = ExcelEnodeb4gSheetMaker()
        self._gnodeb5g_sheet_maker = ExcelGnodeb5gSheetMaker()
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._csht_ccl_service = CshtCclService()
        self._cf_bts_maker = CFBtsMaker()

    def _init_data(self):
        self._bts_all_items_ten_tren_hthong_dict = {}
        self._rp_alarm_items_list_all_raw = []

        self.rp_alarm_items_list_bts_clr = []
        self.rp_alarm_items_list_bts_nclr = []
        self.rp_alarm_items_list_bts_csht_mll_nclr = []
        self.rp_al_item_list_nguon_ac_nclr = []

    def load(self):
        self._init_data()

        #
        self._tht_ttvt_maker.load()
        self._nodeb3g_sheet_maker.load()
        self._enodeb4g_sheet_maker.load()
        self._gnodeb5g_sheet_maker.load()
        self._csht_ccl_service.load()
        self._cf_bts_maker.load()

        #
        self._loadFromExcel()

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

    def _check_ghi_chu(self, delta_time_list) -> list:
        ghi_chu_dict = {
            "tinh": [],
            "vnp": [],
            "ca2": []
        }

        for item_to_check in delta_time_list:
            if (item_to_check[SC.K_VNP_GHI_CHU] != "") and (item_to_check[SC.K_TINH_GHI_CHU] != ""):
                ghi_chu_dict["ca2"].append(item_to_check)
                continue
            if (item_to_check[SC.K_VNP_GHI_CHU] != ""):
                ghi_chu_dict["vnp"].append(item_to_check)
                continue
            if (item_to_check[SC.K_TINH_GHI_CHU] != ""):
                ghi_chu_dict["tinh"].append(item_to_check)
                continue

        #
        if ghi_chu_dict.get("ca2"):
            return ghi_chu_dict["ca2"]

        #
        vnp_items = ghi_chu_dict.get("vnp", [])
        tinh_items = ghi_chu_dict.get("tinh", [])

        if vnp_items:
            if not tinh_items:
                return vnp_items
            #
            has_vnp_priority = any(item[SC.K_LOAI_SU_CO] in ["1", "5"] for item in vnp_items)
            if has_vnp_priority:
                return vnp_items

            has_tinh_priority = any(item[SC.K_LOAI_SU_CO] in ["1", "5"] for item in tinh_items)
            if has_tinh_priority:
                return tinh_items
            #
            has_vnp_priority = any(item[SC.K_LOAI_SU_CO] is not None for item in vnp_items)
            if has_vnp_priority:
                return vnp_items

            has_tinh_priority = any(item[SC.K_LOAI_SU_CO] is not None for item in tinh_items)
            return tinh_items if has_tinh_priority else vnp_items

        if tinh_items:
            return tinh_items

        return delta_time_list

    def _check_ma_loi(self, delta_time_list) -> list:
        ma_loi_dict = {
            "empty": [],
            "1": [],
            "5": [],
            "other": []
        }

        for item_to_check in delta_time_list:
            match str(item_to_check[SC.K_LOAI_SU_CO]):
                case "1":
                    ma_loi_dict["1"].append(item_to_check)
                case "5":
                    ma_loi_dict["5"].append(item_to_check)
                case None:
                    ma_loi_dict["empty"].append(item_to_check)
                case _:
                    ma_loi_dict["other"].append(item_to_check)

        if len(ma_loi_dict["1"]) > 0:
            return ma_loi_dict["1"]

        if len(ma_loi_dict["5"]) > 0:
            return ma_loi_dict["5"]

        if len(ma_loi_dict["other"]) > 0:
            return ma_loi_dict["other"]

        return ma_loi_dict["empty"]

    def _get_one_item_from_duplicated(self, list_items_to_check_delta_time: list):
        if len(list_items_to_check_delta_time) == 0:
            return None

        # 1st : xét ghi chú
        list_items_to_checked_ghi_chu = self._check_ghi_chu(list_items_to_check_delta_time)

        # 2nd : xét mã lỗi
        list_items_to_checked_ma_loi = self._check_ma_loi(list_items_to_checked_ghi_chu)

        # get item have max TG SC.BÁO in list_items_to_checked_ma_loi
        if (len(list_items_to_checked_ma_loi) == 0):
            LoggerUtil.get_logger().error(f'list_items_to_checked_ma_loi cannot be empty')
            return None

        item_keep_after_check_delta_time = max(
            list_items_to_checked_ma_loi, key=lambda x: x[SC.K_TG_CBAO])

        return item_keep_after_check_delta_time

    def _loadFromExcel(self):
        # load items
        items_list_all = ExcelRpAlarmLoader().load_items()
        self._rp_alarm_items_list_all_raw = [item.to_dict() for item in items_list_all]

    def _normalize(self):
        # Normalize data
        ng_nhan_mll_site_set = {
            str(x[SC.K_NGUYEN_NHAN]).lower() for x in self._cf_bts_maker.ng_nhan_mll_site_list}
        ng_nhan_mat_nguon_set = {
            str(x[SC.K_NGUYEN_NHAN]).lower() for x in self._cf_bts_maker.ng_nhan_mat_nguon_ac_list}

        for item in self._rp_alarm_items_list_all_raw:
            if str(item[SC.K_OBJECT]).strip().lower().startswith("nodeb"):
                if str(item[SC.K_HE_THONG]).strip().lower() == T.HeThong._4G.value.lower():
                    item[SC.K_HE_THONG] = T.HeThong._3G.value
            #
            ten_hthong = str(item[SC.K_TEN_NE])
            item[SC.K_TEN_TREN_HE_THONG_COMPACT] = (
                ten_hthong[2:].replace("-", "")
                if ten_hthong
                else ""
            )

            #
            for nn in ng_nhan_mll_site_set:
                if (nn == str(item[SC.K_NGUYEN_NHAN]).lower()) or \
                        (nn in str(item[SC.K_NGUYEN_NHAN]).lower()):
                    if str(item[SC.K_TTHAI_CLR]).lower() == "clr":
                        self.rp_alarm_items_list_bts_clr.append(item)
                    else:
                        self.rp_alarm_items_list_bts_nclr.append(item)
                    continue
            for nn in ng_nhan_mat_nguon_set:
                if str(item[SC.K_TTHAI_CLR]).lower() == "clr":
                    continue # chỉ lấy NCLR
                if (nn == str(item[SC.K_NGUYEN_NHAN]).lower()) or \
                        (nn in str(item[SC.K_NGUYEN_NHAN]).lower()):
                    self.rp_al_item_list_nguon_ac_nclr.append(item)
                    continue

        # filter
        self.rp_alarm_items_list_bts_clr = self._filter_duplicated_ne(self.rp_alarm_items_list_bts_clr)
        self.rp_alarm_items_list_bts_nclr = self._filter_duplicated_ne(self.rp_alarm_items_list_bts_nclr)
        self.rp_al_item_list_nguon_ac_nclr = self._filter_duplicated_ne(self.rp_al_item_list_nguon_ac_nclr)


    def _filter_duplicated_ne(self, rp_al_item_list: list):
        item_list_filltered = []

        dynamic_info = DynamicInfoUtil()
        tgian_cbao = int(dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_TGIAN_CBAO_KEY))
        site: str = dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

        for item in rp_al_item_list[:]:
            # Fillter: TG C.BÁO
            try:
                if (item[SC.K_TG_CBAO] is not None) and (item[SC.K_TG_CBAO] != "") \
                        and (float(item[SC.K_TG_CBAO]) < tgian_cbao):
                    rp_al_item_list.remove(item)
                    continue
            except Exception as e:
                LoggerUtil.get_logger().warning(
                    f'ExcelRpAlarmCbaoMllMaker _normalize : exception {item[SC.K_TEN_NE]} {e}')

            # Fillter: Site
            match site.lower():
                case ST.Site.ALL_SITE.value:
                    pass
                case ST.Site.DONG.value | ST.Site.TAY.value:
                    try:
                        ma_csht = self._bts_all_items_ten_tren_hthong_dict\
                            [(item[SC.K_TEN_TREN_HE_THONG_COMPACT], item[SC.K_HE_THONG])]\
                            [SC.K_MA_CSHT]
                        tht = str(self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[ma_csht]\
                            [SC.K_TEN_DVI_QLY]).lower()
                        if str(self._tht_ttvt_maker.tht_dict[tht][SC.K_SITE1]).lower() != \
                                str(site).lower():
                            rp_al_item_list.remove(item)
                    except Exception as e:
                        LoggerUtil.get_logger().warning(
                            f'ExcelRpAlarmCbaoMllMaker _normalize  : {item[SC.K_TEN_NE]}'
                            f' {SC.K_UI_MSG_NOT_DETECT_SITE}'
                        )
                        if self._ui_set_error_callback is not None:
                            self._ui_set_error_callback(
                                item[SC.K_TEN_NE], SC.K_UI_MSG_NOT_DETECT_SITE)
                        rp_al_item_list.remove(item)
                    continue
                case _:
                    LoggerUtil.get_logger.error("ExcelRpAlarmCbaoMllMaker _normalize : Invalid site")
                    pass

        ################################# Fillter duplicated NE
        # Group by He thong
        items_list_group_by_he_thong_dict = {}
        for item in rp_al_item_list:
            items_list_group_by_he_thong_dict.setdefault(item[SC.K_HE_THONG], []).append(item)

        for item_list_xg_group_by_he_thong in items_list_group_by_he_thong_dict.values():
            # Group by TEN_NE
            items_list_xg_group_by_ten_ne_dict = {}
            for item in item_list_xg_group_by_he_thong:
                items_list_xg_group_by_ten_ne_dict.setdefault(
                    str(item[SC.K_TEN_NE]).replace("-", ""), []
                ).append(item)

            for ne, items_list_xg_group_by_ten_ne in items_list_xg_group_by_ten_ne_dict.items():
                items_list_xg_group_by_ten_ne_dict[ne] = sorted(
                    items_list_xg_group_by_ten_ne_dict[ne],
                    key=lambda x: locale.strxfrm(x[SC.K_TG_SU_CO_1])
                )

                if (len(items_list_xg_group_by_ten_ne_dict[ne]) < 2):
                    continue

                list_items_to_check_delta_time = []
                list_item_to_keep = []
                for i in range(len(items_list_xg_group_by_ten_ne_dict[ne])-1):
                    dt0 = parser.parse(items_list_xg_group_by_ten_ne_dict[ne][i]\
                                       [SC.K_TG_SU_CO_1])
                    dt1 = parser.parse(items_list_xg_group_by_ten_ne_dict[ne][i+1]\
                                       [SC.K_TG_SU_CO_1])

                    delta_t = abs((dt1 - dt0).total_seconds())
                    if delta_t <= 10: # Delta t = 10second
                        for j in range(i, i + 2):
                            list_items_to_check_delta_time.append(items_list_xg_group_by_ten_ne_dict[ne][j])
                    else:
                        item_keep_after_check_delta_time = \
                            self._get_one_item_from_duplicated(list_items_to_check_delta_time)
                        if item_keep_after_check_delta_time is not None:
                            list_item_to_keep.append(item_keep_after_check_delta_time)

                        if i == 0: #in case 2 first item have delta t > 10s
                            list_item_to_keep.append(items_list_xg_group_by_ten_ne_dict[ne][i])

                        ###
                        list_items_to_check_delta_time.clear()
                        list_items_to_check_delta_time.append(items_list_xg_group_by_ten_ne_dict[ne][i+1])

                #case: the final item or all items have delta t < 10s
                if len(list_items_to_check_delta_time) > 0:
                    item_keep_after_check_delta_time = \
                        self._get_one_item_from_duplicated(list_items_to_check_delta_time)
                    if item_keep_after_check_delta_time is not None:
                        list_item_to_keep.append(item_keep_after_check_delta_time)

                #output
                items_list_xg_group_by_ten_ne_dict[ne] = list_item_to_keep

            # output normalized
            for items_list_xg_group_by_ten_ne in items_list_xg_group_by_ten_ne_dict.values():
                for item in items_list_xg_group_by_ten_ne:
                    item_list_filltered.append(item)

        return item_list_filltered