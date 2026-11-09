from logging import Logger
import os
from typing import List, Optional
from numpy import append
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font, PatternFill
from collections import defaultdict
import locale

from backend.repositories.pon.pon_rp_card_access_repo import RpCardAccessService
from backend.repositories.pon.pon_rp_trans_access_repo import RpTransAccessService
from backend.repositories.pon.pon_thbi_access_repo import ThbiAccessService
from backend.repositories.pon.pon_ds_tbao_xgspon_dong_repo import DsTbaoXgsponDongService
from backend.repositories.pon.pon_bc_chi_tiet_onu_repo import BcChTietOnuService
from backend.repositories.cf_thbi_info_repo import ThietBiInfoService

from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker

from backend.constant import type as T
from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import constant as SC
from share.constant import type as ST
from share.util.logger_util import LoggerUtil
from share.util.explorer_util import ExplorerUtil
from share.util.time_util import TimeUtil
from share.util.convert import safe_sort_num, safe_sort_str, safe_sort_value, to_int, to_float

class QlyHsuatGponService:
    """Business logic layer."""

    def __init__(self) -> None:
        locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')

        self._hs_port_pon_dict_by_ten_hthong = None
        self._slg_tbao_sfp = None
        self._gtri_hs_sfp_khuyen_nghi = None
        self._site = None

        self._olt_ui_filtered: set[str] = set()

        self._ds_port_trong_tren_olt: list = []

        self._rp_card_access_service = RpCardAccessService()
        self._rp_trans_access_service = RpTransAccessService()
        self._thbi_access_service = ThbiAccessService()
        self._ds_tbao_xgspon_service = DsTbaoXgsponDongService()
        self._csht_ccl_service = CshtCclService()
        self._bc_chtiet_onu_service = BcChTietOnuService()
        self._thbi_info_service = ThietBiInfoService()

        self._tht_ttvt_service = ExcelThtTtvtMaker()

    def _load_data(self):
        self._site = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

        self._slg_tbao_sfp = to_int(
            DynamicInfoUtil().get_value(
                2, SC.K_SCREEN_INPUT, "slg_tbao_fsp"
            ) or "40", True
        )

        self._gtri_hs_sfp_khuyen_nghi = to_float(
            DynamicInfoUtil().get_value(
                2, SC.K_SCREEN_INPUT, "gtri_hs_sfp_cbao"
            ) or "100", True
        )

        ###

        self._rp_card_access_service.load()
        self._rp_trans_access_service.load()
        self._thbi_access_service.load()
        self._ds_tbao_xgspon_service.load()
        self._csht_ccl_service.load()
        self._bc_chtiet_onu_service.load()
        self._thbi_info_service.load()
        self._tht_ttvt_service.load()

    def _normalize_data(self):
        pass

    def get_preview(self) -> tuple[List[dict], List[dict]]:
        LoggerUtil.get_logger().info(
            f"QlyHsuatGponService get_preview start"
        )

        self._load_data()
        #
        hs_pon_record: List[dict] = self._make_hs_pon_data_list()
        #
        tghop_record: List[dict] = self._make_tghop_data_list()

        LoggerUtil.get_logger().info(
            f"QlyHsuatGponService get_preview complete"
        )

        return hs_pon_record, tghop_record

    def _get_loai_sfp_by_slot(self, ten_hthong, slot, port) -> None | str:
        model_pn = self._rp_trans_access_service.rp_trans_access_dict_by_ten_hthong_slot\
            .get(
                (ten_hthong, str(slot), str(port)), {}
            )\
            .get(
                SC.K_MODEL, None
            )

        if not model_pn:
            model_pn = self._rp_trans_access_service.rp_trans_access_dict_by_ten_hthong_slot\
                .get(
                    (ten_hthong, "", str(port)), {}
                )\
                .get(
                    SC.K_MODEL, None
                )

        if not model_pn:
            return "N/A"
        
        loai_sfp = str(
            self._thbi_info_service.sfp_dict\
            .get(
                model_pn, {}
            )\
            .get(
                SC.K_LOAI_SFP, "N/A"
            )
        )

        return loai_sfp
    
    def _get_port_range_by_card(
        self,
        ten_card: str,
        dong_card: str
    ) -> tuple[int | None, int | None]:
        try:
            loai_port = None

            if str(ten_card).lower() != "onboard":
                loai_port = (
                    self._thbi_info_service.card_dict
                    .get(ten_card, {})
                    .get(SC.K_LOAI_PORT, "N/A")
                )
            else:
                loai_port = (
                    self._thbi_info_service.dong_card_dict
                    .get(dong_card, {})
                    .get(SC.K_LOAI_PORT, "N/A")
                )

            start, end = map(int, loai_port.split("_"))
            return start, end

        except Exception as e:
            LoggerUtil.get_logger().warning(
                f"_get_port_range_by_card ten_card: {ten_card}, dong_card: {dong_card} failed: {e}"
            )
            return None, None
        
    def _valid_site_by_ttvt(self, ttvt: str):
        # Fillter: Site
        match self._site.lower():
            case ST.Site.ALL_SITE.value:
                return True
            case ST.Site.DONG.value | ST.Site.TAY.value:
                try:
                    if str(self._tht_ttvt_service.ttvt_dict[str(ttvt).lower()][SC.K_SITE1]).lower() == \
                            str(self._site).lower():
                        return True
                    else:
                        return False
                except Exception as e:
                    LoggerUtil.get_logger().warning(
                        f'_valid_site_by_ttvt failled : {ttvt}'
                        f' {SC.K_UI_MSG_NOT_DETECT_SITE} as {e}'
                    )
                    return None
            case _:
                LoggerUtil.get_logger.error("_valid_site_by_ttvt : Invalid site")
                return None

        return None

    ###

    def _make_warning_onu_item(self, item_dict: dict) -> list[dict] | None:
        ten_hthong = item_dict.get(SC.K_TEN_HE_THONG, "N/A")

        ma_csht = self._thbi_access_service.thbi_access_dict_by_ten_hthong\
                    .get(ten_hthong, {})\
                    .get(SC.K_MA_CSHT, "N/A")
        
        ttvt = str(
                    self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                    .get(ma_csht, {})\
                    .get(SC.K_TEN_TTVT_TRAM_VT_NETX, "N/A")
                )

        if self._valid_site_by_ttvt(ttvt) == False:
            return None

        ten_csht = str(
                    self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                    .get(ma_csht, {})\
                    .get(SC.K_TEN_CSHT, "N/A")
                )

        ip = self._thbi_access_service.thbi_access_dict_by_ten_hthong\
            .get(ten_hthong, {})\
            .get(SC.K_IP, "N/A")

        item = {
            SC.K_STT: 0,
            SC.K_TEN_HE_THONG: item_dict.get(SC.K_TEN_HE_THONG, "N/A"),
            SC.K_IP: ip,

            SC.K_MA_CSHT: ma_csht,
            SC.K_TEN_CSHT: ten_csht,
            SC.K_TTVT: ttvt,

            SC.K_FRAME: to_int(item_dict.get(SC.K_FRAME, ""), False),
            SC.K_SLOT: to_int(item_dict.get(SC.K_SLOT, "N/A"), False),
            SC.K_PORT: to_int(item_dict.get(SC.K_PORT, "N/A"), False),
            SC.K_ONU: to_int(item_dict.get(SC.K_ONU, "N/A"), False), #Onu idx

            SC.K_SERIAL: item_dict.get(SC.K_SERIAL, ""),
            SC.K_LOAI_ONU: item_dict.get(SC.K_LOAI_ONU, ""),
            SC.K_TEN_ONU: item_dict.get(SC.K_TEN_ONU, ""),
            SC.K_THBAO: item_dict.get(SC.K_THBAO, ""), #Ten ThBao

            SC.K_KH_HANG: item_dict.get(SC.K_KH_HANG, ""), #Tên KH
            SC.K_DIA_CHI: item_dict.get(SC.K_DIA_CHI, ""), #Địa chỉ KH
            SC.K_TRANG_THAI: item_dict.get(SC.K_TRANG_THAI, ""), #Tình trạng
            SC.K_THAM_SO: item_dict.get(SC.K_THAM_SO, ""), #Tham số cổng
            SC.K_DVU: item_dict.get(SC.K_DVU, ""), #Gói dịch vụ

            SC.K_GHI_CHU: item_dict.get(SC.K_GHI_CHU, ""),
        }

        return item

    def _make_warn_onu_list(self) -> list[dict]:
        ret_list : list[dict] = []

        for item in self._bc_chtiet_onu_service.warning_onu_record:
            ret = self._make_warning_onu_item(item)
            if ret is not None:
                ret_list.append(ret)
            else:
                pass

        for item in self._ds_tbao_xgspon_service.warning_xgspon_records:
            ret = self._make_warning_onu_item(item)
            if ret is not None:
                ret_list.append(ret)

        #TTVT-Ma CSHT-IP-Frame-Slot-IP-Frame-Slot-Port-Onu idx
        try:
            ret_list.sort(
                key=lambda x:
                    (
                        safe_sort_str(locale.strxfrm(x.get(SC.K_TTVT))),
                        safe_sort_str(x.get(SC.K_MA_CSHT)),
                        safe_sort_str(x.get(SC.K_IP)),
                        safe_sort_num(x.get(SC.K_FRAME)),
                        safe_sort_num(x.get(SC.K_SLOT)),
                        safe_sort_num(x.get(SC.K_PORT)),
                        safe_sort_num(x.get(SC.K_ONU)),
                    )
            )
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"duplicated_onu sort failed due to {e}"
            )

        counter = 1
        for item in ret_list:
            item[SC.K_STT] = counter
            counter += 1

        return ret_list

    def _make_tg_hop_nguon_onu_item(self, item_dict: dict) -> list[dict] | None:
        ten_hthong = item_dict.get(SC.K_TEN_HE_THONG, "N/A")

        #

        if self._olt_ui_filtered:
            if ten_hthong not in self._olt_ui_filtered:
                return None

        #

        ma_csht = self._thbi_access_service.thbi_access_dict_by_ten_hthong\
                    .get(ten_hthong, {})\
                    .get(SC.K_MA_CSHT, "N/A")
        
        ttvt = str(
                    self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                    .get(ma_csht, {})\
                    .get(SC.K_TEN_TTVT_TRAM_VT_NETX, "N/A")
                )

        valid_ttvt = self._valid_site_by_ttvt(ttvt)
        if valid_ttvt != True:
            match valid_ttvt:
                case None:
                    LoggerUtil.get_logger().warning(
                        f"{self.__class__.__name__} cannot detect side : {item_dict}"
                    )
                case _:
                    pass

            return None
        
        ten_csht = str(
                    self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                    .get(ma_csht, {})\
                    .get(SC.K_TEN_CSHT, "N/A")
                )

        item = {
            SC.K_STT: 0,
            SC.K_TEN_HE_THONG: item_dict.get(SC.K_TEN_HE_THONG, "N/A"),
            SC.K_IP: item_dict.get(SC.K_IP, "N/A"),

            SC.K_MA_CSHT: ma_csht,
            SC.K_TEN_CSHT: ten_csht,
            SC.K_TTVT: ttvt,

            SC.K_FRAME: to_int(item_dict.get(SC.K_FRAME, "N/A"), False),
            SC.K_SLOT: to_int(item_dict.get(SC.K_SLOT, "N/A"), False),
            SC.K_PORT: to_int(item_dict.get(SC.K_PORT, "N/A"), False),
            SC.K_ONU: to_int(item_dict.get(SC.K_ONU, "N/A"), False), #Onu idx

            SC.K_SERIAL: item_dict.get(SC.K_SERIAL, ""),
            SC.K_LOAI_ONU: item_dict.get(SC.K_LOAI_ONU, ""),
            SC.K_TEN_ONU: item_dict.get(SC.K_TEN_ONU, ""),
            SC.K_THBAO: item_dict.get(SC.K_THBAO, ""), #Ten ThBao

            SC.K_KH_HANG: item_dict.get(SC.K_KH_HANG, ""), #Tên KH
            SC.K_DIA_CHI: item_dict.get(SC.K_DIA_CHI, ""), #Địa chỉ KH
            SC.K_TRANG_THAI: item_dict.get(SC.K_TRANG_THAI, ""), #Tình trạng
            SC.K_THAM_SO: item_dict.get(SC.K_THAM_SO, ""), #Tham số cổng
            SC.K_DVU: item_dict.get(SC.K_DVU, ""), #Gói dịch vụ
        }

        return item

    def _make_tg_hop_nguon_onu_list(self) -> list[dict]:
        ret_list : list[dict] = []

        for item in self._bc_chtiet_onu_service.all_valid_onu_record:
            ret = self._make_tg_hop_nguon_onu_item(item)
            if ret is not None:
                ret_list.append(ret)
            else:
                pass

        #TTVT-Ma CSHT-IP-Frame-Slot-IP-Frame-Slot-Port-Onu idx
        try:
            ret_list.sort(
                key=lambda x:
                    (
                        safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT))),
                        safe_sort_value(x.get(SC.K_MA_CSHT)),
                        safe_sort_value(x.get(SC.K_IP)),
                        safe_sort_value(x.get(SC.K_FRAME)),
                        safe_sort_value(x.get(SC.K_SLOT)),
                        safe_sort_value(x.get(SC.K_PORT)),
                        safe_sort_value(x.get(SC.K_ONU)),
                    )
            )
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"tg_hop_nguon_onu sort failed due to {e}"
            )

        counter = 1
        for item in ret_list:
            item[SC.K_STT] = counter
            counter += 1

        return ret_list

    def _make_ds_port_trong_tren_olt_item(self, item_dict: dict) -> list[dict] | None:
        item = None

        port_start, port_end = item_dict.get(SC.K_PORT, (None,None))

        ten_hthong = item_dict.get(SC.K_TEN_HE_THONG, "N/A") #ten hthong
        slot = item_dict.get(SC.K_SLOT, "N/A") #Slot
        port_trong_gpon = ""
        port_trong_mpm = ""
        port_trong_n2 = ""
        port_trong_k_sfp = ""

        port_trong_gpon_list = []
        port_trong_mpm_list = []
        port_trong_n2_list = []
        port_trong_k_sfp_list = []

        for port in range(0, 17):
            if isinstance(port_start, int) and isinstance(port_end, int):
                if port not in range(port_start, port_end+1):
                    continue

            sfp = item_dict.get(f'sfp_{port}', "N/A")
            tbao = item_dict.get(f'tb_{port}', "N/A")
            full_slot = f"{slot}/{port}"

            if isinstance(sfp, str) and isinstance(tbao, (int, float)):
                if tbao == 0:
                    match sfp.lower():
                        case SC.K_GPON:
                            port_trong_gpon = f"{port_trong_gpon}, {full_slot}" if port_trong_gpon != "" else full_slot
                            port_trong_gpon_list.append(full_slot)
                        case SC.K_MPM:
                            port_trong_mpm = f"{port_trong_mpm}, {full_slot}" if port_trong_mpm != "" else full_slot
                            port_trong_mpm_list.append(full_slot)
                        case SC.K_N2:
                            port_trong_n2: str = f"{port_trong_n2}, {full_slot}" if port_trong_n2 != "" else full_slot
                            port_trong_n2_list.append(full_slot)
                        case _:
                            LoggerUtil.get_logger().error(
                                f"{self.__class__.__name__} _make_ds_port_trong_tren_olt_item {ten_hthong} sfp unkown: {sfp}"
                            )
            else:
                port_trong_k_sfp = f"{port_trong_k_sfp}, {full_slot}" if port_trong_k_sfp != "" else full_slot
                port_trong_k_sfp_list.append(full_slot)

        if any(x != "" for x in [port_trong_gpon, port_trong_mpm, port_trong_n2, port_trong_k_sfp]):
            item = {
                "port_trong_gpon_list": port_trong_gpon_list,
                "port_trong_mpm_list": port_trong_mpm_list,
                "port_trong_n2_list": port_trong_n2_list,
                "port_trong_k_sfp_list": port_trong_k_sfp_list,

                SC.K_STT: 0, #STT
                SC.K_TEN_HE_THONG: ten_hthong, #Ten Hthong
                SC.K_IP: item_dict.get(SC.K_IP, "N/A"), #IP
                SC.K_LOAI_OLT: item_dict.get(SC.K_LOAI_OLT, "N/A"), #Loai OLT
                SC.K_MA_CSHT: item_dict.get(SC.K_MA_CSHT, "N/A"), #MA CSHT
                SC.K_TEN_CSHT: item_dict.get(SC.K_TEN_CSHT, "N/A"), #Ten CSHT
                SC.K_TTVT: item_dict.get(SC.K_TTVT, "N/A"), #TTVT
                SC.K_FRAME: item_dict.get(SC.K_FRAME, "N/A"), #Frame
                SC.K_SLOT: item_dict.get(SC.K_SLOT, "N/A"), #Frame
                SC.K_TEN_CARD: item_dict.get(SC.K_TEN_CARD, "N/A"), #Ten card
                SC.K_LOAI_CARD: item_dict.get(SC.K_LOAI_CARD, "N/A"), #Loai card
                SC.K_GPON: port_trong_gpon,
                SC.K_MPM: port_trong_mpm,
                SC.K_N2: port_trong_n2,
                "port_trong_k_sfp": port_trong_k_sfp,
            }

            return item
        
        return None

    def _make_ds_port_trong_tren_olt_list(self, item_list: list[dict]) -> list[dict]:
        ret_list : list[dict] = []

        for item in item_list:
            ret = self._make_ds_port_trong_tren_olt_item(item)
            if ret is not None:
                ret_list.append(ret)
            else:
                pass

        try:
            ret_list.sort(
                key=lambda x:
                    (
                        safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT))),
                        safe_sort_value(x.get(SC.K_MA_CSHT)),
                        safe_sort_value(x.get(SC.K_IP)),
                        safe_sort_value(x.get(SC.K_FRAME)),
                        safe_sort_value(x.get(SC.K_SLOT)),
                    )
            ) #TTVT-Ma CSHT-IP-Frame-Slot
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"ds_port_trong_tren_olt sort failed due to {e}"
            )

        counter = 1
        for item in ret_list:
            item[SC.K_STT] = counter #STT
            counter += 1

        return ret_list

    def _make_ds_tbi_can_toi_uu_pon_item(self, item_dict: dict) -> list[dict] | None:
        ret_list: list[dict] = []

        port_start, port_end = item_dict.get(SC.K_PORT, (None,None))

        #Port
        for port in range(0, 17):
            if isinstance(port_start, int) and isinstance(port_end, int):
                if port not in range(port_start, port_end+1):
                    continue

            slg_tbao = item_dict.get(f'tb_{port}', "N/A")
            sfp = item_dict.get(f'sfp_{port}', "N/A")
            if isinstance(slg_tbao, (int, float)):
                hs = round(
                    float(slg_tbao / self._slg_tbao_sfp),
                    4
                )

                if hs*100 > float(self._gtri_hs_sfp_khuyen_nghi):
                    item = {
                        SC.K_STT: 0, #STT
                        SC.K_TEN_HE_THONG: item_dict.get(SC.K_TEN_HE_THONG, "N/A"), #Ten Hthong
                        SC.K_IP: item_dict.get(SC.K_IP, "N/A"), #IP
                        SC.K_LOAI_OLT: item_dict.get(SC.K_LOAI_OLT, "N/A"), #Loai OLT
                        SC.K_MA_CSHT: item_dict.get(SC.K_MA_CSHT, "N/A"), #MA CSHT
                        SC.K_TEN_CSHT: item_dict.get(SC.K_TEN_CSHT, "N/A"), #Ten CSHT
                        SC.K_TTVT: item_dict.get(SC.K_TTVT, "N/A"), #TTVT
                        SC.K_FRAME: item_dict.get(SC.K_FRAME, "N/A"), #Frame
                        SC.K_SLOT: item_dict.get(SC.K_SLOT, "N/A"), #Slot
                        SC.K_TEN_CARD: item_dict.get(SC.K_TEN_CARD, "N/A"), #Ten card
                        SC.K_LOAI_CARD: item_dict.get(SC.K_LOAI_CARD, "N/A"), #Loai card

                        SC.K_LOAI_SFP: sfp, #Loai sfp

                        SC.K_PORT: port,
                        SC.K_SL_THBAO: slg_tbao,
                        SC.K_HS: hs,
                        SC.K_DE_XUAT: "",

                        SC.K_GHI_CHU: ""
                    }

                    ret_list.append(item)

        return ret_list

    def _fill_port_de_xuat_chuyen_tbao(self, tbi_can_toi_uu_pon_list: list[dict]) -> list[dict]:
        #
        ds_thbi_can_toi_uu_pon_csht_dict = defaultdict(list)
        ds_thbi_can_toi_uu_pon_ten_hthong_dict = defaultdict(list)

        ds_thbi_can_toi_uu_pon_ten_hthong_port_dict = {} #save output here

        for item in tbi_can_toi_uu_pon_list:
            ten_hthong = item.get(SC.K_TEN_HE_THONG, "N/A") #Ten Hthong
            frame = item.get(SC.K_FRAME, "N/A") #Frame
            slot = item.get(SC.K_SLOT, "N/A") #Slot
            port = item.get(SC.K_PORT, "N/A") #Port
            ma_csht = item.get(SC.K_MA_CSHT, "N/A") #Ma CSHT

            ds_thbi_can_toi_uu_pon_csht_dict[ma_csht].append(item)
            ds_thbi_can_toi_uu_pon_ten_hthong_dict[ten_hthong].append(item)

            ds_thbi_can_toi_uu_pon_ten_hthong_port_dict[(ten_hthong, frame, slot, port)] = item

        # tong hop port trong
        port_trong_gpon_list: list[tuple] = []
        port_trong_mpm_list: list[tuple] = []
        port_trong_n2_list: list[tuple] = []
        port_trong_k_sfp_list: list[tuple] = []

        for item in self._ds_port_trong_tren_olt:
            ten_hthong = item.get(SC.K_TEN_HE_THONG, "N/A")

            for port_trong in item.get("port_trong_gpon_list", []):
                port_trong_gpon_list.append((port_trong, SC.K_GPON, ten_hthong))

            for port_trong in item.get("port_trong_mpm_list", []):
                port_trong_mpm_list.append((port_trong, SC.K_MPM, ten_hthong))

            for port_trong in item.get("port_trong_n2_list", []):
                port_trong_n2_list.append((port_trong, SC.K_N2, ten_hthong))

            for port_trong in item.get("port_trong_k_sfp_list", []):
                port_trong_k_sfp_list.append((port_trong, "port_trong_k_sfp", ten_hthong))

        def _match_ports(port_trong_list: list[tuple], allowed_sfp_types: list[str] | None, scope: str, ghi_chu_prefix: str):
            for port_trong_info in port_trong_list[:]:
                port_trong, loai_sfp_trong, ten_hthong = port_trong_info

                if scope == "olt":
                    candidates = ds_thbi_can_toi_uu_pon_ten_hthong_dict.get(ten_hthong, [])
                else:
                    ma_csht = self._thbi_access_service.thbi_access_dict_by_ten_hthong \
                        .get(ten_hthong, {}).get(SC.K_MA_CSHT, None)
                    if not ma_csht:
                        continue
                    # Khac OLT, cung CSHT
                    candidates = [
                        it for it in ds_thbi_can_toi_uu_pon_csht_dict.get(ma_csht, [])
                        if it.get(SC.K_TEN_HE_THONG) != ten_hthong
                    ]

                if not candidates:
                    continue

                matched_candidates = []
                if allowed_sfp_types is not None:
                    for sfp_type in allowed_sfp_types:
                        matched_candidates = [
                            it for it in candidates
                            if str(it.get(SC.K_LOAI_SFP, "")).lower() == sfp_type
                        ]
                        if matched_candidates:
                            break
                else:
                    matched_candidates = candidates

                if not matched_candidates:
                    continue

                matched_candidates.sort(
                    key=lambda x: safe_sort_num(x.get(SC.K_HS)),
                    reverse=True,
                )
                target = matched_candidates[0]

                target_ten_hthong = target.get(SC.K_TEN_HE_THONG)
                target_frame = target.get(SC.K_FRAME)
                target_slot = target.get(SC.K_SLOT)
                target_port = target.get(SC.K_PORT)
                target_ma_csht = target.get(SC.K_MA_CSHT)

                # remove port trong
                port_trong_list.remove(port_trong_info)

                # remove thbi can toi uu
                if target in ds_thbi_can_toi_uu_pon_csht_dict.get(target_ma_csht, []):
                    ds_thbi_can_toi_uu_pon_csht_dict[target_ma_csht].remove(target)
                if target in ds_thbi_can_toi_uu_pon_ten_hthong_dict.get(target_ten_hthong, []):
                    ds_thbi_can_toi_uu_pon_ten_hthong_dict[target_ten_hthong].remove(target)

                # out put
                target_key = (target_ten_hthong, target_frame, target_slot, target_port)
                if target_key in ds_thbi_can_toi_uu_pon_ten_hthong_port_dict:
                    scope_text = "cùng OLT" if scope == "olt" else "khác OLT"
                    ds_thbi_can_toi_uu_pon_ten_hthong_port_dict[target_key][SC.K_DE_XUAT] = f"{port_trong} {ten_hthong}"
                    ds_thbi_can_toi_uu_pon_ten_hthong_port_dict[target_key][SC.K_GHI_CHU] = f"{ghi_chu_prefix}, {scope_text}"

        # De xuat port:
        ## 1. cung OLT
        _match_ports(port_trong_gpon_list, [SC.K_GPON], scope="olt", ghi_chu_prefix="GPON")
        _match_ports(port_trong_n2_list, [SC.K_N2], scope="olt", ghi_chu_prefix="N2")
        _match_ports(port_trong_mpm_list, [SC.K_MPM, SC.K_GPON], scope="olt", ghi_chu_prefix="MPM")
        _match_ports(port_trong_k_sfp_list, None, scope="olt", ghi_chu_prefix="chưa gắn SFP")

        ## 2. khac OLT, cung CSHT
        _match_ports(port_trong_gpon_list, [SC.K_GPON], scope="csht", ghi_chu_prefix="GPON")
        _match_ports(port_trong_n2_list, [SC.K_N2], scope="csht", ghi_chu_prefix="N2")
        _match_ports(port_trong_mpm_list, [SC.K_MPM, SC.K_GPON], scope="csht", ghi_chu_prefix="MPM")
        _match_ports(port_trong_k_sfp_list, None, scope="csht", ghi_chu_prefix="chưa gắn SFP")

        return list(ds_thbi_can_toi_uu_pon_ten_hthong_port_dict.values())

    def _make_ds_tbi_can_toi_uu_pon_list(self, item_list: list[dict]) -> list[dict]:
        ret_list : list[dict] = []

        for item in item_list:
            ret = self._make_ds_tbi_can_toi_uu_pon_item(item)
            if ret is not None:
                ret_list.extend(ret)
            else:
                pass

        ###
        ret_list = self._fill_port_de_xuat_chuyen_tbao(ret_list)

        ### sort
        try:
            ret_list.sort(
                key=lambda x:
                    (
                        safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT))),
                        safe_sort_value(x.get(SC.K_MA_CSHT)),
                        safe_sort_value(x.get(SC.K_IP)),
                        safe_sort_value(x.get(SC.K_FRAME)),
                        safe_sort_value(x.get(SC.K_SLOT)),
                    )
            ) #TTVT-Ma CSHT-IP-Frame-Slot
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"ds_tbi_can_toi_uu_pon sort failed due to {e}"
            )

        counter = 1
        for item in ret_list:
            item[SC.K_STT] = counter #STT
            counter += 1

        return ret_list

    def _make_bc_sl_hs_pon_item(self, item_dict: dict):
        item = {
            SC.K_STT: 0, #STT
            SC.K_TEN_HE_THONG: item_dict.get(SC.K_TEN_HE_THONG, "N/A"), #Ten Hthong
            SC.K_IP: item_dict.get(SC.K_IP, "N/A"), #IP
            SC.K_LOAI_OLT: item_dict.get(SC.K_LOAI_OLT, "N/A"), #Loai OLT
            SC.K_MA_CSHT: item_dict.get(SC.K_MA_CSHT, "N/A"), #Ma CSHT
            SC.K_TEN_CSHT: item_dict.get(SC.K_TEN_CSHT, "N/A"), #Ten CSHT
            SC.K_TTVT: item_dict.get(SC.K_TTVT, "N/A"), #Don vi | TTVT
            SC.K_FRAME: item_dict.get(SC.K_FRAME, "N/A"), #Frame
            SC.K_SLOT: item_dict.get(SC.K_SLOT, "N/A"), #SLOT | CARD
        }

        port_start, port_end = item_dict.get(SC.K_PORT, (None,None))

        for port in range(0, 17):
            if isinstance(port_start, int) and isinstance(port_end, int):
                if port not in range(port_start, port_end+1):
                    item[f'tb_{port}'] = 'X'
                    item[f'hs_{port}'] = 'X'

                    continue

            #
            slg_tbao = item_dict.get(f'tb_{port}', "N/A")
            item[f'tb_{port}'] = slg_tbao

            if isinstance(slg_tbao, (int, float)):
                hs = round(
                    float(slg_tbao / self._slg_tbao_sfp),
                    4
                )

                item[f'hs_{port}'] = hs
            else:
                item[f'hs_{port}'] = ""

        return item

    def _make_bc_sl_hs_pon_list(self, hs_pon_list: list[dict]) -> list[dict]:
        ret_list : list[dict] = []

        for item in hs_pon_list:
            ret_item = self._make_bc_sl_hs_pon_item(item)
            if ret_item is not None:
                ret_list.append(ret_item)
            else:
                LoggerUtil.get_logger().error(
                    f"_make_bc_sl_hs_pon_list cannot make item: {item}"
                )

        try:
            ret_list.sort(
                key=lambda x:
                    (
                        safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT))),
                        safe_sort_value(x.get(SC.K_MA_CSHT)),
                        safe_sort_value(x.get(SC.K_IP)),
                        safe_sort_value(x.get(SC.K_FRAME)),
                        safe_sort_value(x.get(SC.K_SLOT)),
                    )
            ) #TTVT-Ma CSHT-IP-Frame-SLOT
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"bc_sl_hs_pon sort failed due to {e}"
            )

        counter = 1
        for item in ret_list:
            item[SC.K_STT] = counter
            counter += 1

        return ret_list
    
    def _make_olt_port_xtb_item(self, item_dict: dict):
        ret_list = []

        ten_hthong = item_dict.get(SC.K_TEN_HE_THONG, "N/A")
        so_onu_toi_da = self._slg_tbao_sfp

        for port in range(0, 17):
            slg_tbao = item_dict.get(f'tb_{port}', "N/A")

            if isinstance(slg_tbao, (int, float)):
                if slg_tbao > self._slg_tbao_sfp:

                    item = {
                        1: 0, #STT
                        2: ten_hthong, #Ten Hthong
                        3: item_dict.get(SC.K_IP, "N/A"), #IP
                        4: item_dict.get(SC.K_LOAI_OLT, "N/A"), #Loai
                        5: item_dict.get(SC.K_MA_CSHT, "N/A"), #Ma CSHT
                        6: item_dict.get(SC.K_TEN_CSHT, "N/A"), #Ten CSHT
                        7: item_dict.get(SC.K_TTVT, "N/A"), #Don vi
                        8: item_dict.get(SC.K_FRAME, "N/A"), #Frame
                        9: item_dict.get(SC.K_SLOT, "N/A"), #SLOT | CARD
                        10: port, #PORT
                        11: slg_tbao, #Đã dùng
                        12: so_onu_toi_da, #Tg số Onu tối đa
                    }

                    #Hieu suat
                    item[13] = float(
                        round(
                            float(slg_tbao) / float(so_onu_toi_da),
                            4
                        )
                    )

                    ret_list.append(item)

        return ret_list

    def _make_olt_port_xtb_list(self, hs_pon_list: list[dict]):
        ret_list : list[dict] = []

        for item in hs_pon_list:
            ret = self._make_olt_port_xtb_item(item)
            if ret is not None:
                ret_list.extend(ret)
            else:
                LoggerUtil.get_logger().error(
                    f"_make_olt_port_xtb_list cannot make item: {item}"
                )

        try:
            ret_list.sort(
                key=lambda x:
                    (
                        safe_sort_value(locale.strxfrm(x.get(7))),
                        safe_sort_value(x.get(5)),
                        safe_sort_value(x.get(3)),
                        safe_sort_value(x.get(8)),
                        safe_sort_value(x.get(9)),
                        safe_sort_value(x.get(10)),
                    )
            ) #TTVT-Ma CSHT-IP-Frame-Slot-PORT
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"olt_port_xtb sort failed due to {e}"
            )

        counter = 1
        for item in ret_list:
            item[1] = counter #STT
            counter += 1

        return ret_list
    
    def _make_hs_sdung_xgspon_item(self, item_dict: dict):
        loai_card = item_dict.get(SC.K_LOAI_CARD, "N/A")
        if str(loai_card).lower() == "combo":
            pass
        else:
            return None

        ten_hthong = item_dict.get(SC.K_TEN_HE_THONG, "N/A")
        slot = item_dict.get(SC.K_SLOT, "N/A")

        item = {
            1: 0, #STT
            2: ten_hthong, #Ten Hthong
            3: item_dict.get(SC.K_IP, "N/A"), #IP
            4: item_dict.get(SC.K_LOAI_OLT, "N/A"), #Loai
            5: item_dict.get(SC.K_MA_CSHT, "N/A"), #Ma CSHT
            6: item_dict.get(SC.K_TEN_CSHT, "N/A"), #Ten CSHT
            7: item_dict.get(SC.K_TTVT, "N/A"), #Don vi

            8: item_dict.get(SC.K_FRAME, "N/A"), #FRAME
            9: slot, #SLOT
            10: item_dict.get(SC.K_TEN_CARD, "N/A"), #Tên Card
            11: loai_card, #Loại card
        }

        so_cong_mpm = item_dict.get(SC.K_MPM, "N/A")
        so_cong_n2 = item_dict.get(SC.K_N2, "N/A")

        item[70] = so_cong_mpm #mpm
        item[71] = so_cong_n2 #n2

        item[12] = to_int(so_cong_mpm) + to_int(so_cong_n2) #Số cổng gắn SFP XGSPON

        item[13] = 0 #Số cổng XGSPON sử dụng
        item[14] = 0 #Số TB XGSPON sử dụng

        item[66] = 0  # <= 30%
        item[67] = 0  # > 30% - <= 70%
        item[68] = 0  # > 70% - <= 90%
        item[69] = 0  # > 90%

        port_start, port_end = item_dict.get(SC.K_PORT, (None,None))

        #Port/Hiệu suất (tính theo x TB trên 1 port)
        #(GPON, XGSP), ...
        i = 15
        for port in range(0, 17):
            if isinstance(port_start, int) and isinstance(port_end, int):
                if port not in range(port_start, port_end+1):
                    item[i] = 'X'
                    item[i + 1] = 'X'
                    item[i + 2] = 'X'

                    i += 3

                    continue

            loai_sfp = item_dict.get(f'sfp_{port}', "N/A")
            slg_tbao = item_dict.get(f'tb_{port}', "N/A")
            slg_tbao_xgspon = self._ds_tbao_xgspon_service.ds_thbao_xgspon_dict_by_ten_hthong_port\
                .get((ten_hthong, str(slot), str(port)), {})\
                .get(SC.K_SL_THBAO, 0)
            match str(loai_sfp).lower():
                case SC.K_GPON | SC.K_MPM | SC.K_N2:
                    item[i] = loai_sfp
                    item[i + 1] = slg_tbao - slg_tbao_xgspon
                    item[i + 2] = slg_tbao_xgspon
                case "kxd":
                    item[i] = "KXD"
                    item[i + 1] = "KXD"
                    item[i + 2] = "KXD"
                case "":
                    item[i] = ""
                    item[i + 1] = ""
                    item[i + 2] = ""
                case _:
                    item[i] = "N/A"
                    item[i + 1] = "N/A"
                    item[i + 2] = "N/A"

            #
            if isinstance(item[i + 2], (int, float)):
                #
                if slg_tbao_xgspon > 0:
                    item[13] += 1
                    item[14] += slg_tbao_xgspon

                #
                hs = 100 * slg_tbao_xgspon / self._slg_tbao_sfp

                if hs <= 30:
                    item[66] += 1
                elif hs <= 70:
                    item[67] += 1
                elif hs <= 90:
                    item[68] += 1
                else:
                    item[69] += 1

            i += 3

        return item
    
    def _make_hs_sdung_xgspon_data_list(self, hs_pon_list: list[dict]):
        ret_list : list[dict] = []

        for item in hs_pon_list:
            ret_item = self._make_hs_sdung_xgspon_item(item)
            if ret_item is not None:
                ret_list.append(ret_item)
            else:
                pass

        try:
            ret_list.sort(
                key=lambda x:
                    (
                        safe_sort_value(locale.strxfrm(x.get(7))),
                        safe_sort_value(x.get(5)),
                        safe_sort_value(x.get(3)),
                        safe_sort_value(x.get(8)),
                        safe_sort_value(x.get(9)),
                    )
            ) #TTVT-Ma CSHT-IP-Frame-SLOT
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"hs_sdung_xgspon sort failed due to {e}"
            )

        counter = 1
        for item in ret_list:
            item[1] = counter #STT
            counter += 1

        return ret_list

    def _make_hs_pon_ten_hthong_list(self, ten_hthong: str):
        ret_list : list[dict] = []

        #

        if self._olt_ui_filtered:
            if ten_hthong not in self._olt_ui_filtered:
                return ret_list

        #

        ma_csht = self._thbi_access_service.thbi_access_dict_by_ten_hthong\
                    .get(ten_hthong, {})\
                    .get(SC.K_MA_CSHT, "N/A")
        
        ttvt = str(
                    self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                    .get(ma_csht, {})\
                    .get(SC.K_TEN_TTVT_TRAM_VT_NETX, "N/A")
                )

        if self._valid_site_by_ttvt(ttvt) != True:
            return ret_list

        #

        ip = self._thbi_access_service.thbi_access_dict_by_ten_hthong\
                    .get(ten_hthong, {})\
                    .get(SC.K_IP, "N/A")

        loai_olt = self._thbi_access_service.thbi_access_dict_by_ten_hthong\
                    .get(ten_hthong, {})\
                    .get(SC.K_DONG, "N/A") #ZTEC600\

        ten_csht = str(
                    self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                    .get(ma_csht, {})\
                    .get(SC.K_TEN_CSHT, "N/A")
                )

        #

        frame_set: set = self._rp_card_access_service.\
            rp_card_access_dict_by_ten_hthong.get(ten_hthong, {}).get(SC.K_FRAME, set())
        slot_set: set = self._rp_card_access_service.\
            rp_card_access_dict_by_ten_hthong.get(ten_hthong, {}).get(SC.K_SLOT, set())

        for frame in frame_set:
            for slot in slot_set:
                port_dict: dict = self._bc_chtiet_onu_service.bc_chtiet_onu_dict_by_ten_hthong\
                    .get(ten_hthong, {}).get(frame, {}).get(slot, {})

                port_start = None
                port_end = None
                ten_card: str = None
                loai_card = None

                #
                card_by_slot_only = self._rp_card_access_service\
                    .rp_card_access_dict_by_ten_hthong_slot_only\
                    .get(
                        (ten_hthong, f'{slot}'), {}
                    )

                ## Filter Serial
                last_serial_card = card_by_slot_only.get(SC.K_LAST_SERIAL, "N/A")
                last_valid_serial_card = card_by_slot_only.get(SC.K_LAST_VALID_SERIAL, "N/A")
                if last_serial_card in ["", None]:
                    if last_valid_serial_card in ["", None]:
                        LoggerUtil.get_logger().warning(
                            f"{self.__class__.__name__} {ten_hthong} slot: {slot} : Card chưa từng có Serial"
                        )

                        continue

                ##
                dong_card = card_by_slot_only \
                    .get(
                        SC.K_DONG, None
                    )

                if not dong_card:
                    LoggerUtil.get_logger().warning(
                        f"QlyHsuatGponService _make_hs_pon_ten_hthong_list: unkown dong_card"
                        f" {ten_hthong} frame: {frame} slot: {slot} port_dict: {str(port_dict)}"
                    )
                
                ##
                ten_card = card_by_slot_only \
                    .get(
                        SC.K_TEN_CARD, "N/A"
                    )
                    
                #
                if ten_card and (str(ten_card).lower() != "onboard"):
                    loai_card = self._thbi_info_service.card_dict\
                            .get(ten_card, {})\
                            .get(SC.K_LOAI_CARD, "N/A")
                else:
                    loai_card = self._thbi_info_service.dong_card_dict\
                            .get(dong_card, {})\
                            .get(SC.K_LOAI_CARD, "N/A")
                    
                #
                port_start, port_end = self._get_port_range_by_card(
                    ten_card, dong_card
                )

                #
                item = {
                    SC.K_PORT: (port_start, port_end),

                    SC.K_STT: 0,
                    SC.K_TEN_HE_THONG: ten_hthong,
                    SC.K_IP: ip,
                    SC.K_LOAI_OLT: loai_olt,
                    SC.K_MA_CSHT: ma_csht,
                    SC.K_TEN_CSHT: ten_csht,
                    SC.K_TTVT: ttvt,
                    SC.K_FRAME: frame,
                    SC.K_SLOT: slot,
                    SC.K_TEN_CARD: ten_card,
                    SC.K_LOAI_CARD: loai_card,
                }

                # SL cong toi da
                try:
                    item[SC.K_SL_CONG] = int(port_end) - int(port_start) + 1
                except:
                    item[SC.K_SL_CONG] = 0

                # Serial number
                item[SC.K_SERIAL] = last_valid_serial_card

                item[SC.K_CONG_PON] = 0 #Số cổng PON sử dụng
                item[SC.K_ONT] = 0 #Số ONT sử dụng

                item[SC.K_HSUAT_2] = 0  # HS <= 30%
                item[SC.K_HSUAT_3] = 0  # HS > 30% - <= 70%
                item[SC.K_HSUAT_4] = 0  # HS > 70% - <= 90%
                item[SC.K_HSUAT_5] = 0  # HS > 90%

                item[SC.K_GPON] = 0 #Tghop GPON
                item[SC.K_MPM] = 0 #Tghop MPM
                item[SC.K_N2] = 0 #Tghop N2

                # (Loại SFP | SL) ...
                for port in range(0, 17):
                    if isinstance(port_start, int) and isinstance(port_end, int):
                        if port not in range(port_start, port_end+1):
                            item[f'sfp_{port}'] = 'X'
                            item[f'tb_{port}'] = 'X'

                            continue

                    loai_sfp = self._get_loai_sfp_by_slot(
                        ten_hthong, slot, port
                    )

                    item[f'sfp_{port}'] = loai_sfp
                    item[f'tb_{port}'] = port_dict.get(port, {}).get(SC.K_ONU, "")
                    
                    #nomalize
                    match str(item[f'sfp_{port}']).lower():
                        # "Loai"
                        case "n/a":
                            if item[f'tb_{port}'] == 0 or item[f'tb_{port}'] == "":
                                item[f'sfp_{port}'] = ""
                            else:
                                item[f'sfp_{port}'] = "KXD"

                        # "SL"
                        case "":
                            item[f'tb_{port}'] = ""
                        case SC.K_GPON | SC.K_MPM | SC.K_N2:
                            if item[f'tb_{port}'] == "":
                                item[f'tb_{port}'] = 0

                    if isinstance(item[f'tb_{port}'], (int, float)):
                        ###
                        if item[f'tb_{port}'] > 0:
                            item[SC.K_CONG_PON] += 1  #Số cổng PON sử dụng
                        item[SC.K_ONT] +=  item[f'tb_{port}'] #Số ONT sử dụng

                        ### HS
                        hs = 100 * item[f'tb_{port}'] / self._slg_tbao_sfp

                        if hs <= 30:
                            item[SC.K_HSUAT_2] += 1
                        elif hs <= 70:
                            item[SC.K_HSUAT_3] += 1
                        elif hs <= 90:
                            item[SC.K_HSUAT_4] += 1
                        else:
                            item[SC.K_HSUAT_5] += 1

                    # Tghop GPON|MPM|N2
                    match str(item[f'sfp_{port}']).lower():
                        case SC.K_GPON:
                            item[SC.K_GPON] += 1
                            continue
                        case SC.K_MPM:
                            item[SC.K_MPM] += 1
                            continue
                        case SC.K_N2:
                            item[SC.K_N2] += 1

                #Số cổng gắn SFP
                item[SC.K_SFP] = item[SC.K_GPON] + item[SC.K_MPM] + item[SC.K_N2]

                ret_list.append(item)

        return ret_list

    def _make_hs_pon_data_list(self) -> List[dict]:
        item_list : list[dict] = []

        for item in self._thbi_access_service.all_record:
            ten_he_thong = item.get(SC.K_TEN_HE_THONG, None)
            if ".olt." in ten_he_thong.lower():
                ret_list: list[dict] = self._make_hs_pon_ten_hthong_list(ten_he_thong)
                if len(ret_list) > 0:
                    item_list.extend(ret_list)

        try:
            item_list.sort(
                key=lambda x:
                    (
                        safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT))),
                        safe_sort_value(x.get(SC.K_MA_CSHT)),
                        safe_sort_value(x.get(SC.K_IP)),
                        safe_sort_value(x.get(SC.K_FRAME)),
                        safe_sort_value(x.get(SC.K_SLOT)),
                    )
            ) #TTVT-Ma CSHT-IP-Frame-SLOT
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"hs_pon sort failed due to {e}"
            )

        counter = 1
        for item in item_list:
            item[SC.K_STT] = counter
            counter += 1

        # prepare data for TgHop
        self._hs_port_pon_dict_by_ten_hthong = defaultdict(
            lambda: {
                SC.K_ONT: 0, #Số ONT sử dụng
                SC.K_CARD: 0, #Số card thuê bao lắp đặt
                SC.K_SFP: 0, #SFP LDAT | Số cổng PON gắn SFP
                SC.K_CONG_PON: 0, #SL SFP PON sử dụng | Số cổng PON sử dụng
            }
        )

        for item in item_list:
            ten_hthong = item[SC.K_TEN_HE_THONG]

            self._hs_port_pon_dict_by_ten_hthong[ten_hthong][SC.K_ONT] += item[SC.K_ONT]
            self._hs_port_pon_dict_by_ten_hthong[ten_hthong][SC.K_CARD] += 1
            self._hs_port_pon_dict_by_ten_hthong[ten_hthong][SC.K_SFP] += item[SC.K_SFP]
            self._hs_port_pon_dict_by_ten_hthong[ten_hthong][SC.K_CONG_PON] += item[SC.K_CONG_PON]

        return item_list

    def _make_tghop_data_item(self, ten_he_thong: str) -> Optional[dict]:
        try:
            if self._olt_ui_filtered:
                if ten_he_thong not in self._olt_ui_filtered:
                    return None

            #

            ma_csht = self._thbi_access_service.thbi_access_dict_by_ten_hthong\
                .get(ten_he_thong, {})\
                .get(SC.K_MA_CSHT, "N/A")

            ttvt = str(
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                .get(ma_csht, {})\
                .get(SC.K_TEN_TTVT_TRAM_VT_NETX, "N/A")
            )

            if self._valid_site_by_ttvt(ttvt) != True:
                return None

            item: dict = {
                SC.K_STT: 0,

                SC.K_MA_TINH: "GLI",

                SC.K_LOAI_OLT: self._thbi_access_service.thbi_access_dict_by_ten_hthong
                    .get(ten_he_thong, {})\
                    .get(SC.K_DONG, "N/A"),

                SC.K_TEN_HE_THONG: ten_he_thong,

                SC.K_IP: self._thbi_access_service.thbi_access_dict_by_ten_hthong\
                    .get(ten_he_thong, {})\
                    .get(SC.K_IP, "N/A"),

                #Vị trí card XGSPON
                SC.K_VTRI_CARD_XGSPON: self._rp_card_access_service.rp_card_access_dict_by_ten_hthong\
                    .get(ten_he_thong, {})\
                    .get(SC.K_VTRI_CARD_XGSPON, ''),

                SC.K_MA_CSHT: ma_csht,
                SC.K_TTVT: ttvt,
                SC.K_TEN_CSHT: str(
                    self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                    .get(ma_csht, {})\
                    .get(SC.K_TEN_CSHT, "N/A")
                ),
                SC.K_PHUONG_XA: str(
                    self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                    .get(ma_csht, {})\
                    .get(SC.K_PHUONG_XA, "N/A")
                ),
            }

            item_hs_pon_dict = self._hs_port_pon_dict_by_ten_hthong\
                .get(ten_he_thong, {})

            #Tên Card XGSPON
            item[SC.K_TEN_CARD_XGSPON] = ""
            ten_card_set: set =  self._rp_card_access_service.rp_card_access_dict_by_ten_hthong\
                .get(ten_he_thong, {})\
                .get(SC.K_TEN_CARD_XGSPON, '')
            for card_name in ten_card_set:
                item[SC.K_TEN_CARD_XGSPON] = (
                    f"{item[SC.K_TEN_CARD_XGSPON]}, {card_name}"
                    if item[SC.K_TEN_CARD_XGSPON]
                    else card_name
                )

            #Số lượng card XGSPON
            item[SC.K_SL_CARD_XGSPON] = self._rp_card_access_service.rp_card_access_dict_by_ten_hthong\
                .get(ten_he_thong, {})\
                .get(SC.K_SL_CARD_XGSPON, 0)
            item[SC.K_SL_CARD_XGSPON] = to_int(item[SC.K_SL_CARD_XGSPON])

            #SL SFP XGSPON lắp đặt
            item[SC.K_SL_SFP_XGSPON] = self._rp_trans_access_service\
                .rp_trans_access_dict_by_ten_hthong.get(ten_he_thong, {})\
                .get(SC.K_SL_SFP_XGSPON, 0)
            item[SC.K_SL_SFP_XGSPON] = to_int(item[SC.K_SL_SFP_XGSPON])

            #SL TB XGSPON
            item[SC.K_SL_TB_XGSPON] = self._ds_tbao_xgspon_service.ds_thbao_xgspon_dict_by_ten_hthong\
                .get(ten_he_thong, {})\
                .get(SC.K_SL_THBAO, 0)
            item[SC.K_SL_TB_XGSPON] = to_int(item[SC.K_SL_TB_XGSPON])

            #Số card thuê bao lắp đặt
            item[SC.K_CARD_PON] = item_hs_pon_dict.get(SC.K_CARD, 0)

            #Số cổng PON gắn SFP
            item[SC.K_CONG_PON] = item_hs_pon_dict.get(SC.K_SFP, 0)

            #SL SFP PON sử dụng / Số cổng PON sử dụng
            item[SC.K_SU_DUNG_1] = item_hs_pon_dict.get(SC.K_CONG_PON, 0)

            #Số ONT sử dụng
            item[SC.K_ONT] = item_hs_pon_dict.get(SC.K_ONT, 0)

        except Exception as e:
            LoggerUtil.get_logger().error(
                f"QlyHsuatGponService _make_tghop_data_item: failed : {ten_he_thong} due to {e}"
            )
            return None

        try:
            item[SC.K_HSUAT_1] = float(
                round(
                    float(item[SC.K_SL_TB_XGSPON]) / (
                            float(item[SC.K_SL_SFP_XGSPON])*self._slg_tbao_sfp
                    ),
                    4
                )
            )
        except Exception as e:
            item[SC.K_HSUAT_1] = 0

        return item

    def _make_tghop_data_list(self) -> List[dict]:
        ret_list: List[dict] = []
        #
        for item in self._thbi_access_service.all_record:
            ten_he_thong = item.get(SC.K_TEN_HE_THONG, None)
            if ".olt." in ten_he_thong.lower():
                ret_item = self._make_tghop_data_item(ten_he_thong)
                if ret_item:
                    ret_list.append(ret_item)

        try:
            ret_list.sort(
                key=lambda x:
                    (
                        safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT))),
                        safe_sort_value(x.get(SC.K_MA_CSHT)),
                        safe_sort_value(x.get(SC.K_IP)),
                    )
            )
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"tghop sort failed due to {e}"
            )

        counter = 1
        for item in ret_list:
            item[SC.K_STT] = counter
            counter += 1

        return ret_list
    
    def _write_to_hs_pon_sheet(self, ws: Worksheet, data_list: list[dict]):
        HEADER_1 = [
            SC.K_STT, SC.K_TEN_HE_THONG,
            SC.K_IP, SC.K_LOAI_OLT, SC.K_MA_CSHT, SC.K_TEN_CSHT,
            SC.K_TTVT,

            SC.K_FRAME, SC.K_SLOT, SC.K_TEN_CARD,
            SC.K_SL_CONG, SC.K_SERIAL,
            SC.K_LOAI_CARD,

            SC.K_SFP, #Số cổng gắn SFP
            SC.K_CONG_PON, #SL SFP PON sử dụng | Số cổng PON sử dụng
            SC.K_ONT, #Số ONT sử dụng
        ]

        HEADER_2 = [
            name
            for port in range(17)
            for name in (f"sfp_{port}", f"tb_{port}")
        ]

        HEADER_3 = [
            SC.K_HSUAT_2, # HS <= 30%
            SC.K_HSUAT_3, # HS > 30% - <= 70%
            SC.K_HSUAT_4, # HS > 70% - <= 90%
            SC.K_HSUAT_5, # HS > 90%

            SC.K_GPON, #Tghop GPON
            SC.K_MPM, #Tghop MPM
            SC.K_N2, #Tghop N2
        ]

        HEADER = HEADER_1 + HEADER_2 + HEADER_3

        for row_idx, item in enumerate(data_list, start=5):
            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

                #
                if "sfp_" in key:
                    if isinstance(value, str):
                        cell.font = Font(size=10, italic=True)

                #
                if str(value).lower() == 'x':
                    cell.fill = PatternFill(
                        start_color="EAEAEA", end_color="EAEAEA", fill_type="solid"
                    )
                    cell.value = ""
    
    def write_to_tghop_sheet(self, ws: Worksheet, data_list: list[dict]):
        HEADER = [
            SC.K_STT, SC.K_MA_TINH, SC.K_TEN_HE_THONG,
            SC.K_IP, SC.K_LOAI_OLT, SC.K_MA_CSHT, SC.K_TEN_CSHT,
            SC.K_PHUONG_XA, SC.K_TTVT,

            SC.K_CARD_PON, SC.K_CONG_PON, SC.K_SU_DUNG_1,

            SC.K_ONT,
            
            SC.K_SL_CARD_XGSPON,
            SC.K_VTRI_CARD_XGSPON, SC.K_TEN_CARD_XGSPON,

            SC.K_SL_SFP_XGSPON, SC.K_SL_TB_XGSPON,
            SC.K_HSUAT_1,
        ]

        hs_col_idx = 19 # Hiệu suất %

        ws.cell(row=2, column=hs_col_idx,
                value=(
                    f"Hiệu suất %\n"
                    f"(2) / ((1) * {self._slg_tbao_sfp})"
                )
        )

        for row_idx, item in enumerate(data_list, start=4):
            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

                #
                if col_idx == hs_col_idx:
                    if isinstance(value, (int, float)):
                        cell.number_format = T.percentage_number_format(value)
                        cell.alignment = T.EX_FORMAT_ALIGNMENT_RIGHT

    def _write_to_hs_sdung_xgspon_sheet(self, ws: Worksheet, data_list: list[dict]):
        for row_idx, item in enumerate(data_list, start=5):
            for col_idx in range(1, 72):
                key = col_idx
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

                if str(value).lower() == 'x':
                    cell.fill = PatternFill(
                        start_color="EAEAEA", end_color="EAEAEA", fill_type="solid"
                    )
                    cell.value = ""
                else:
                    if col_idx >= 15 and col_idx <= 66 and col_idx % 3 == 2:
                        cell.fill = PatternFill(
                            start_color="DDF0C8", end_color="DDF0C8", fill_type="solid"
                        )

                if col_idx >= 15 and col_idx <= 66 and col_idx % 3 == 0:
                    if isinstance(value, str):
                        cell.font = Font(size=10, italic=True)

    def _write_to_olt_port_xtb_sheet(self, ws: Worksheet, data_list: list[dict]):
        hs_idx = 13

        for row_idx, item in enumerate(data_list, start=3):
            for col_idx in range(1, 14):
                key = col_idx
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

                #
                if col_idx == hs_idx:
                    if isinstance(value, (int, float)):
                        cell.number_format = T.percentage_number_format(value)
                        cell.alignment = T.EX_FORMAT_ALIGNMENT_RIGHT

    def _write_to_bc_sl_hs_pon_sheet(self, ws: Worksheet, data_list: list[dict]):
        HEADER_1 = [
            SC.K_STT, SC.K_TEN_HE_THONG,
            SC.K_IP, SC.K_LOAI_OLT, SC.K_MA_CSHT, SC.K_TEN_CSHT,
            SC.K_TTVT,

            SC.K_FRAME, SC.K_SLOT,
        ]

        HEADER_2 = [
            name
            for port in range(17)
            for name in (f"tb_{port}", f"hs_{port}")
        ]

        HEADER = HEADER_1 + HEADER_2

        #
        ws.cell(
            row=1, column=10, value=f"Port/Hiệu suất (tính theo {self._slg_tbao_sfp} TB trên 1 port)"
        )

        #
        for row_idx, item in enumerate(data_list, start=4):
            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

                #
                if "hs_" in key:
                    if isinstance(value, (int, float)):
                        cell.number_format = T.percentage_number_format(value)
                        cell.alignment = T.EX_FORMAT_ALIGNMENT_RIGHT

                #
                if str(value).lower() == 'x':
                    cell.fill = PatternFill(
                        start_color="EAEAEA", end_color="EAEAEA", fill_type="solid"
                    )
                    cell.value = ""

    def _write_to_ds_tbi_can_toi_uu_pon_sheet(self, ws: Worksheet, data_list: list[dict]):
        HEADER = [
            SC.K_STT, SC.K_TEN_HE_THONG, SC.K_IP,
            SC.K_LOAI_OLT, SC.K_MA_CSHT, SC.K_TEN_CSHT,
            SC.K_TTVT,
            SC.K_FRAME, SC.K_SLOT, SC.K_TEN_CARD, SC.K_LOAI_CARD,
            SC.K_PORT,
            SC.K_SL_THBAO, SC.K_HS, SC.K_DE_XUAT,
            SC.K_GHI_CHU,
        ]

        gtri_hs_sfp_khuyen_nghi_text = f"{round(to_float(self._gtri_hs_sfp_khuyen_nghi), 2):g}"
        #
        ws.cell(
            row=1, column=12, value=f"Hiệu suất > {gtri_hs_sfp_khuyen_nghi_text}%"
        )

        #
        for row_idx, item in enumerate(data_list, start=4):
            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

                #
                if key == SC.K_HS:
                    if isinstance(value, (int, float)):
                        cell.number_format = T.percentage_number_format(value)
                        cell.alignment = T.EX_FORMAT_ALIGNMENT_RIGHT

                if key == SC.K_DE_XUAT and str(value).lower() == "":
                    cell.fill = PatternFill(
                        start_color="D6FFC1", end_color="D6FFC1", fill_type="solid"
                    )

    def _write_to_ds_port_trong_tren_olt_sheet(self, ws: Worksheet, data_list: list[dict]):
        HEADER = [
            SC.K_STT, SC.K_TEN_HE_THONG, SC.K_IP,
            SC.K_LOAI_OLT,
            SC.K_MA_CSHT, SC.K_TEN_CSHT,
            SC.K_TTVT,
            SC.K_FRAME, SC.K_SLOT,
            SC.K_TEN_CARD, SC.K_LOAI_CARD,
            SC.K_GPON, SC.K_MPM, SC.K_N2,
            "port_trong_k_sfp"
        ]
        fit_width_keys = [SC.K_GPON, SC.K_MPM, SC.K_N2, "port_trong_k_sfp"]
        #
        for row_idx, item in enumerate(data_list, start=4):
            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

                if key in fit_width_keys:
                    cell.number_format = T.EX_NUMBER_FORMAT_TEXT

        #
        fit_width_cols = [
            HEADER.index(key) + 1
            for key in fit_width_keys
        ]

        ExcelHandleUtil().auto_fit_columns(
            ws,
            col_idx_list=fit_width_cols,
            start_row=4,
            end_row=3 + len(data_list),
            min_width=18,
            max_width=300,
        )

    def _write_to_tg_hop_nguon_onu_sheet(self, ws: Worksheet, data_list: list[dict]):
        #
        HEADER = [
            SC.K_STT, SC.K_TEN_HE_THONG, SC.K_IP,
            SC.K_MA_CSHT, SC.K_TEN_CSHT,
            SC.K_TTVT,
            SC.K_FRAME, SC.K_SLOT, SC.K_PORT, SC.K_ONU,
            SC.K_SERIAL, SC.K_LOAI_ONU, SC.K_TEN_ONU, SC.K_THBAO,
            SC.K_KH_HANG, SC.K_DIA_CHI, SC.K_TRANG_THAI, SC.K_THAM_SO, SC.K_DVU,
        ]

        for row_idx, item in enumerate(data_list, start=3):
            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

    def _write_to_warn_onu_sheet(self, ws: Worksheet, data_list: list[dict]):
        #
        HEADER = [
            SC.K_STT, SC.K_TEN_HE_THONG, SC.K_IP,
            SC.K_MA_CSHT, SC.K_TEN_CSHT,
            SC.K_TTVT,
            SC.K_FRAME, SC.K_SLOT, SC.K_PORT, SC.K_ONU,
            SC.K_SERIAL, SC.K_LOAI_ONU, SC.K_TEN_ONU, SC.K_THBAO,
            SC.K_KH_HANG, SC.K_DIA_CHI, SC.K_TRANG_THAI, SC.K_THAM_SO, SC.K_DVU,
            SC.K_GHI_CHU,
        ]

        for row_idx, item in enumerate(data_list, start=3):
            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

    def export_to_excel(self, filtered_record: List[dict], output_path: str) -> str|None:
        LoggerUtil.get_logger().info(
            f"QlyHsuatGponService export_to_excel start"
        )
        hien_trg_file_path = ""
        de_xuat_file_path = ""

        if filtered_record:
            self._olt_ui_filtered = {
                item[SC.K_TEN_HE_THONG]
                for item in filtered_record
            }

        #
        if os.path.isdir(output_path):
            os.makedirs(output_path, exist_ok=True)
            site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1) or ""
            if site.lower() == ST.Site.ALL_SITE.value:
                site = "2Site"
            #
            hien_trg_file_name = (
                f"Quản Lý Hiệu Suất Mạng GPON VNPT GLI_Hiện trạng"
                f"_{site}"
                f"_{TimeUtil().get_detail_current_time_str().replace(':', '').replace('/', '') or ''}"
                f".xlsx"
            )
            hien_trg_file_path = os.path.join(output_path, hien_trg_file_name)

            de_xuat_file_name = (
                f"Quản Lý Hiệu Suất Mạng GPON VNPT GLI_Đề xuất"
                f"_{site}"
                f"_{TimeUtil().get_detail_current_time_str().replace(':', '').replace('/', '') or ''}"
                f".xlsx"
            )
            de_xuat_file_path = os.path.join(output_path, de_xuat_file_name)
        else:
            LoggerUtil.get_logger().error(
                f"{self.__class__.__name__} output_path must a folder"
            )
            raise RuntimeError

        #
        excel_output_hien_trang_template_path = \
            ExplorerUtil().get_output_template_file_path(
                f"Quản lý hiệu suất GPON-hiện trạng-template.xlsx"
            )

        ret = ExplorerUtil().cp_to_folder(
            excel_output_hien_trang_template_path,
            os.path.dirname(hien_trg_file_path),
            os.path.basename(hien_trg_file_path),
        )

        if ret is None or ret != hien_trg_file_path:
            LoggerUtil.get_logger().error(
                f"QlyHsuatGponService export_to_excel failed create hien_trang ret_path = {ret}, filepath = {hien_trg_file_path}"
            )
            raise RuntimeError

        #
        excel_output_de_xuat_template_path = \
            ExplorerUtil().get_output_template_file_path(
                f"Quản lý hiệu suất GPON-đề xuất-template.xlsx"
            )

        ret = ExplorerUtil().cp_to_folder(
            excel_output_de_xuat_template_path,
            os.path.dirname(de_xuat_file_path),
            os.path.basename(de_xuat_file_path),
        )

        if ret is None or ret != de_xuat_file_path:
            LoggerUtil.get_logger().error(
                f"QlyHsuatGponService export_to_excel failed create de_xuat ret_path = {ret}, filepath = {de_xuat_file_path}"
            )
            raise RuntimeError

        self._load_data()

        self._normalize_data()

        ### hien trang
        try:
            wb_hien_trang = openpyxl.load_workbook(hien_trg_file_path)
            #
            hs_pon_list: List[dict] = self._make_hs_pon_data_list()
            ws = wb_hien_trang["HS_PON"]
            self._write_to_hs_pon_sheet(ws, hs_pon_list)

            #
            hs_sdung_xgspon_list: List[dict] = self._make_hs_sdung_xgspon_data_list(hs_pon_list)
            ws = wb_hien_trang["HS_SD_XGSPON"]
            self._write_to_hs_sdung_xgspon_sheet(ws, hs_sdung_xgspon_list)

            olt_port_xtb_list: List[dict] = self._make_olt_port_xtb_list(hs_pon_list)
            ws = wb_hien_trang["OLT port >xTB"]
            self._write_to_olt_port_xtb_sheet(ws, olt_port_xtb_list)
            ws.title = f"OLT port >{self._slg_tbao_sfp}TB"

            #
            tghop_list: List[dict] = self._make_tghop_data_list()
            ws = wb_hien_trang["TỔNG HỢP"]
            self.write_to_tghop_sheet(ws, tghop_list)

            #
            tg_hop_nguon_onu: List[dict] = self._make_tg_hop_nguon_onu_list()
            ws = wb_hien_trang["Tổng hợp nguồn Onu"]
            self._write_to_tg_hop_nguon_onu_sheet(ws, tg_hop_nguon_onu)

            warn_onu: List[dict] = self._make_warn_onu_list()
            ws = wb_hien_trang["DS cảnh báo"]
            self._write_to_warn_onu_sheet(ws, warn_onu)

        except Exception as e:
            LoggerUtil.get_logger().error(
                f"QlyHsuatGponService export_to_excel hien_trang failed: {e}"
            )
            raise RuntimeError
        finally:
            try:
                wb_hien_trang.save(hien_trg_file_path)
                wb_hien_trang.close()
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'QlyHsuatGponService: unable to close workbook hien_trang: {e}'
                )
                raise RuntimeError

        ### de xuat
        try:
            wb_de_xuat = openpyxl.load_workbook(de_xuat_file_path)

            #
            bc_sl_hs_pon_list: List[dict] = self._make_bc_sl_hs_pon_list(hs_pon_list)
            ws = wb_de_xuat["BC SL hiệu suất PON"]
            self._write_to_bc_sl_hs_pon_sheet(ws, bc_sl_hs_pon_list)

            self._ds_port_trong_tren_olt: List[dict] = self._make_ds_port_trong_tren_olt_list(hs_pon_list)
            ws = wb_de_xuat["DS port trống trên OLT"]
            self._write_to_ds_port_trong_tren_olt_sheet(ws, self._ds_port_trong_tren_olt)

            ds_tbi_can_toi_uu_pon_list: List[dict] = self._make_ds_tbi_can_toi_uu_pon_list(hs_pon_list)
            ws = wb_de_xuat["DS thiết bị cần tối ưu PON"]
            self._write_to_ds_tbi_can_toi_uu_pon_sheet(ws, ds_tbi_can_toi_uu_pon_list)

        except Exception as e:
            LoggerUtil.get_logger().error(
                f"QlyHsuatGponService export_to_excel de_xuat failed: {e}"
            )
            raise RuntimeError
        finally:
            try:
                wb_de_xuat.save(de_xuat_file_path)
                wb_de_xuat.close()
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'QlyHsuatGponService: unable to close workbook de_xuat: {e}'
                )
                raise RuntimeError

        ###

        LoggerUtil.get_logger().info(
            f"QlyHsuatGponService export_to_excel finish"
        )

        return output_path