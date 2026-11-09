from dateutil import parser
import locale

from backend.constant import type as T
from backend.repositories.bc_bts.excel_enodeb4g_repo import ExcelEnodeb4gService
from backend.repositories.bc_bts.excel_gnodeb5g_repo import ExcelGnodeb5gService
from backend.repositories.bc_bts.excel_nodeb3g_repo import ExcelNodeb3gService
from backend.repositories.bc_bts.cf_bts_repo import CFBtsRepo
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.util.ex_handle_util import ExcelHandleUtil

from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import constant as SC
from share.constant import type as ST
from share.util.explorer_util import ExplorerUtil

class DataSheet:
    def __init__(self):
        self._tt = None
        self._muc = None
        self._loai_ne = None
        self._ten_ne = None
        self._ten_goi_nho = None
        self._object = None
        self._bsc_rnc = None
        self._nnhan = None
        self._nha_cc = None
        self._tgian_su_co = None
        self._tgian_clr = None
        self._tgain_cbao = None
        self._trthai_clr = None
        self._ma_cbao = None
        self._ch_tiet = None
        self._tinh_tp = None
        self._quan_huyen = None
        self._vnp_ghi_chu = None
        self._tinh_ghi_chu = None
        self._loai_su_co = None
        self._phan_loai_tram = None
        self._time_ac = None
        self._he_thong = None
        self._global_id = None
        self._tgian_tao_tren_fms = None
        self._dvi_qly = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TT: self._tt,
            SC.K_MUC: self._muc,
            SC.K_LOAI_NE: self._loai_ne,
            SC.K_TEN_NE: self._ten_ne,
            SC.K_TEN_GOI_NHO: self._ten_goi_nho,
            SC.K_OBJECT: self._object,
            SC.K_BSC_RNC: self._bsc_rnc,
            SC.K_NGUYEN_NHAN: self._nnhan,
            SC.K_NHA_CC: self._nha_cc,
            SC.K_TG_SU_CO_1: self._tgian_su_co,
            SC.K_TG_CLR: self._tgian_clr,
            SC.K_TG_CBAO: self._tgain_cbao,
            SC.K_TTHAI_CLR: self._trthai_clr,
            SC.K_MA_CBAO: self._ma_cbao,
            SC.K_DETAIL: self._ch_tiet,
            SC.K_TINH_TP: self._tinh_tp,
            SC.K_QUAN_HUYEN: self._quan_huyen,
            SC.K_VNP_GHI_CHU: self._vnp_ghi_chu,
            SC.K_TINH_GHI_CHU: self._tinh_ghi_chu,
            SC.K_LOAI_SU_CO: self._loai_su_co,
            SC.K_PHAN_LOAI_TRAM: self._phan_loai_tram,
            SC.K_TIME_AC: self._time_ac,
            SC.K_HE_THONG: self._he_thong,
            SC.K_GLOBAL_ID: self._global_id,
            SC.K_TGIAN_TAO_TREN_FMS: self._tgian_tao_tren_fms,
            SC.K_DVI_QLY: self._dvi_qly,
        }

    def load(self, item_dic):
        self._tt = item_dic.get("TT")
        self._muc = item_dic.get("MỨC")
        self._loai_ne = item_dic.get("LOẠI NE")
        self._ten_ne = item_dic.get("TÊN NE")
        self._ten_goi_nho = item_dic.get("TÊN GỢI NHỚ")
        self._object = item_dic.get("OBJECT")
        self._bsc_rnc = item_dic.get("BSC/RNC")
        self._nnhan = item_dic.get("N.NHÂN")
        self._nha_cc = item_dic.get("NHÀ CC")
        self._tgian_su_co = item_dic.get("TG SỰ CỐ")
        self._tgian_clr = item_dic.get("TG CLR")
        self._tgain_cbao = item_dic.get("TG C.BÁO")
        self._trthai_clr = item_dic.get("T.THÁI CLR")
        self._ma_cbao = item_dic.get("MÃ CB")
        self._ch_tiet = item_dic.get("CHI TIẾT")
        self._tinh_tp = item_dic.get("TỈNH/TP")
        self._quan_huyen = item_dic.get("QUẬN/HUYỆN")
        self._vnp_ghi_chu = item_dic.get("VNP-GHI CHÚ")
        self._tinh_ghi_chu = item_dic.get("TỈNH GHI CHÚ")
        self._loai_su_co = item_dic.get("LOẠI SỰ CỐ")
        self._phan_loai_tram = item_dic.get("PHÂN LOẠI TRẠM")
        self._time_ac = item_dic.get("TIME AC")
        self._he_thong = item_dic.get("HỆ THỐNG")
        self._global_id = item_dic.get("GLOBALID")
        self._tgian_tao_tren_fms = item_dic.get("TG TẠO TRÊN FMS")
        self._dvi_qly = item_dic.get("ĐƠN VỊ QUẢN LÝ")

        return self

class ExcelRpAlarmLoader:
    def __init__(self):
        pass

    def load_items(self):
        record_list: list[dict] = []
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_RP_ALARM_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_DATA, SC.K_NAME
        )

        for sheet_name in sheet_names:
            excel_path = ExplorerUtil().get_cache_file_path(
                DynamicInfoUtil().get_value(2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_NAME)
            )
            ret_list = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_DATA,
                excel_info_key=SC.K_EXCEL_RP_AL_BC_CBAO_MLL_KEY,
                excel_path=excel_path
            )
            record_list.extend(ret_list)

        return [DataSheet().load(x) for x in record_list]

class ExcelRpAlarmCbaoMllService():
    def __init__(self, ui_set_error_callback=None):
        locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')
        
        self._ui_set_error_callback = ui_set_error_callback
        self._init_data()

        self._nodeb3g_sheet_maker = ExcelNodeb3gService()
        self._enodeb4g_sheet_maker = ExcelEnodeb4gService()
        self._gnodeb5g_sheet_maker = ExcelGnodeb5gService()
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._csht_ccl_service = CshtCclService()
        self._cf_bts_maker = CFBtsRepo()

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
                    f'ExcelRpAlarmCbaoMllService _normalize : exception {item[SC.K_TEN_NE]} {e}')

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
                            f'ExcelRpAlarmCbaoMllService _normalize  : {item[SC.K_TEN_NE]}'
                            f' {SC.K_UI_MSG_NOT_DETECT_SITE}'
                        )
                        if self._ui_set_error_callback is not None:
                            self._ui_set_error_callback(
                                item[SC.K_TEN_NE], SC.K_UI_MSG_NOT_DETECT_SITE)
                        rp_al_item_list.remove(item)
                    continue
                case _:
                    LoggerUtil.get_logger.error("ExcelRpAlarmCbaoMllService _normalize : Invalid site")
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