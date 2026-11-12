import locale
import shutil
import os
from collections import defaultdict
import numpy as np
import re
from typing import DefaultDict
from pathlib import Path
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.drawing.image import Image
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime, timedelta, timezone #date,
from dateutil import parser
import matplotlib
# Use a non-GUI backend to avoid starting a Matplotlib GUI from background threads
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from backend.constant import type as T
from backend.repositories.bc_bts.excel_bc_cbao_mll_repo import ExcelBcCbaoMllService
from backend.util.database_util import DatabaseFactory
from backend.repositories.bc_bts.excel_nodeb3g_repo import ExcelNodeb3gService
from backend.repositories.bc_bts.excel_enodeb4g_repo import ExcelEnodeb4gService
from backend.repositories.bc_bts.excel_gnodeb5g_repo import ExcelGnodeb5gService
from backend.repositories.bc_bts.excel_dmoi_qly_csht_repo import ExcelDmoiQlyCshtService
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.repositories.bc_bts.cf_bts_repo import CFBtsRepo
from backend.repositories.bc_bts.excel_rp_al_cb_mll_repo import ExcelRpAlarmCbaoMllService
from backend.constant import excel_struct_info as ESI
from backend.util.ex_handle_util import ExcelHandleUtil

from share.constant import constant as SC
from share.constant import type as ST
from share.session import Session
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.convert import safe_sort_date_time, safe_sort_num, safe_sort_value, to_int, safe_sort_str
from share.util.convert import to_float

class BcCbaoMllService:
    def __init__(self, ui_set_error_callback=None):
        locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')

        self._ui_set_error_callback = ui_set_error_callback
        self._init_data()

        self._db_adapter = DatabaseFactory.create_adapter()
        self._nodeb3g_sheet_maker = ExcelNodeb3gService()
        self._enodeb4g_sheet_maker = ExcelEnodeb4gService()
        self._gnodeb5g_sheet_maker = ExcelGnodeb5gService()
        self._dmoi_qly_csht_maker = ExcelDmoiQlyCshtService()
        self._csht_ccl_service = CshtCclService()
        self._rp_al_cbao_mll_maker = ExcelRpAlarmCbaoMllService(ui_set_error_callback)
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._cf_bts_maker = CFBtsRepo()
        self._bc_nclr_maker = ExcelBcCbaoMllService()

    def _init_data(self):
        # TGHOP BTS
        self._data_tghop_bts_xg_dict = \
            defaultdict(list)

        self._data_tghop_bts_list = []

        self._bts_counter_by_ttvt_dict = \
            defaultdict(
                lambda: defaultdict(int)
            )

        # MLL CLR
        self._data_bc_cbao_mll_clr_xg_dict = \
            defaultdict(DataBcCbaoMllXgStruct)

        # MLL NCLR
        self._data_bc_cbao_mll_bts_xg_nclr_list = []
        self._data_bc_mat_nguon_ac_nclr_list = []
        self._data_bc_csht_mll_nclr_list = []
        self._data_bc_tghop_nclr_list = []

        self._need_cpare_nclr = DynamicInfoUtil().get_value(
            2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT
        )

        self._site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

        self._sel_rp_type: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_REPORT_TYPE) or ""

    def _prepare_data(self):
        self._nodeb3g_sheet_maker.load()
        self._enodeb4g_sheet_maker.load()
        self._gnodeb5g_sheet_maker.load()
        self._dmoi_qly_csht_maker.load()
        self._csht_ccl_service.load()
        if self._sel_rp_type != ST.ReportTypeInfo.TGHOP_BTS.report_id.name:
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
                safe_sort_value(locale.strxfrm(x.get(SC.K_UI_TO_HA_TANG))),
                safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT_2))),
                safe_sort_value(locale.strxfrm(x.get(SC.K_NE))),
                safe_sort_date_time(x.get(SC.K_UI_TG_SU_CO2), "%d/%m/%Y %H:%M:%S"),
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

    def _make_thgke_bts_chi_tiet_xg_item(self, xg_item_dict: dict, ttvt: str) -> dict:
        item = {
            SC.K_TO_HA_TANG: self._tht_ttvt_maker.ttvt_dict\
                .get(ttvt.strip().lower(), {})\
                .get(SC.K_TO_HA_TANG, ""),
            SC.K_TTVT: ttvt,

            SC.K_TRANG_THAI_HDONG: xg_item_dict.get(SC.K_TRANG_THAI_HDONG, "N/A"),
            SC.K_MA_CSHT: xg_item_dict.get(SC.K_MA_CSHT, "N/A"),
            SC.K_TEN_HE_THONG: xg_item_dict.get(SC.K_TEN_TREN_HE_THONG, "N/A"),
            SC.K_TEN_QUAN_LY: xg_item_dict.get(SC.K_TEN_QUAN_LY, "N/A"),

            SC.K_TRTHAI_DAT_MNO: xg_item_dict.get(SC.K_TRTHAI_DAT_MNO, "N/A"),

            SC.K_LOAI_TRAM: xg_item_dict.get(SC.K_LOAI_TRAM, "N/A"),
            SC.K_BG_TAN: xg_item_dict.get(SC.K_BG_TAN, "N/A"),
            SC.K_NGAY_DUYET: xg_item_dict.get(SC.K_NGAY_DUYET, "N/A"),
            SC.K_SERVICE_IP: xg_item_dict.get(SC.K_SERVICE_IP, "N/A"),
            SC.K_OAM_IP: xg_item_dict.get(SC.K_OAM_IP, "N/A"),

            SC.K_IP_GW_OAM: xg_item_dict.get(SC.K_IP_GW_OAM, ""),
            SC.K_SERVICE_IP_GW: xg_item_dict.get(SC.K_SERVICE_IP_GW, ""),
            SC.K_SERVICE_VLAN: xg_item_dict.get(SC.K_SERVICE_VLAN, ""),
            SC.K_OAM_VLAN: xg_item_dict.get(SC.K_OAM_VLAN, ""),
        }

        return item

    def _make_thgke_bts_chi_tiet_xg(self):
        for he_thong in [T.HeThong._3G.value, T.HeThong._4G.value, T.HeThong._5G.value]:
            match he_thong:
                case T.HeThong._3G.value:
                    bts_xg_items_list_latest = \
                        self._nodeb3g_sheet_maker.nodeb3g_items_list_all
                case T.HeThong._4G.value:
                    bts_xg_items_list_latest = \
                        self._enodeb4g_sheet_maker.enodeb4g_items_list_all
                case T.HeThong._5G.value:
                    bts_xg_items_list_latest = \
                        self._gnodeb5g_sheet_maker.gnodeb5g_items_list_all

            for item in bts_xg_items_list_latest:
                ttvt = ""
                ttvt_lower = ""
                

                try:
                    ttvt = str(
                                    self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                                    [item[SC.K_MA_CSHT]][SC.K_TEN_TTVT_TRAM_VT_NETX]
                                )
                    ttvt_lower = ttvt.strip().lower()

                    site: str = self._tht_ttvt_maker.ttvt_dict\
                        [ttvt_lower][SC.K_SITE1]
                    if self._site.lower() == ST.Site.ALL_SITE.value:
                        pass
                    elif self._site.lower() not in str(site).lower():
                        continue

                except KeyError as e:
                    LoggerUtil.get_logger().warning(
                        f'BcCbaoMllService tghop_bts failed {e}'
                    )

                ret_xg_item = self._make_thgke_bts_chi_tiet_xg_item(
                    item, ttvt
                )
                self._data_tghop_bts_xg_dict[he_thong].append(ret_xg_item)

                self._bts_counter_by_ttvt_dict[ttvt_lower][he_thong] += 1

                if he_thong == T.HeThong._5G.value:
                    bang_tan = item[SC.K_BG_TAN]
                    match str(bang_tan).strip().lower():
                        case "nr3700":
                            self._bts_counter_by_ttvt_dict[ttvt_lower]["nr3700"] +=1
                        case "nr700":
                            self._bts_counter_by_ttvt_dict[ttvt_lower]["nr700"] +=1
                        case _:
                            self._bts_counter_by_ttvt_dict[ttvt_lower]["nrkxd"] +=1

        for he_thong in [T.HeThong._3G.value, T.HeThong._4G.value, T.HeThong._5G.value]:
            self._data_tghop_bts_xg_dict[he_thong].sort(
                key=lambda x: (
                    safe_sort_str(locale.strxfrm(x.get(SC.K_TO_HA_TANG, ""))),
                    safe_sort_str(locale.strxfrm(x.get(SC.K_TTVT, ""))),
                    safe_sort_str(locale.strxfrm(x.get(SC.K_MA_CSHT, ""))),
                    safe_sort_str(locale.strxfrm(x.get(SC.K_TEN_HE_THONG, ""))),
                )
            )

    def _make_thgke_tghop(self) -> None:
        for ttvt_dict in self._tht_ttvt_maker.ttvt_list:
            if self._site.lower() == ST.Site.ALL_SITE.value:
                pass
            elif self._site.lower() not in str(ttvt_dict[SC.K_SITE1]).lower():
                continue

            ttvt = str(ttvt_dict[SC.K_TTVT]).strip().lower()

            item = {
                SC.K_TO_HA_TANG: ttvt_dict[SC.K_TO_HA_TANG],
                SC.K_TTVT: ttvt_dict[SC.K_TTVT],
                SC.K_3G: self._bts_counter_by_ttvt_dict[ttvt][T.HeThong._3G.value],
                SC.K_4G: self._bts_counter_by_ttvt_dict[ttvt][T.HeThong._4G.value],
                SC.K_5G: self._bts_counter_by_ttvt_dict[ttvt][T.HeThong._5G.value],
            }

            self._data_tghop_bts_list.append(item)

        self._data_tghop_bts_list.sort(
            key=lambda x: (
                safe_sort_str(locale.strxfrm(x.get(SC.K_TO_HA_TANG, ""))),
                safe_sort_str(locale.strxfrm(x.get(SC.K_TTVT, ""))),
            )
        )

        # Unknown TTVT
        unknown_ttvt = [
            x for x in self._bts_counter_by_ttvt_dict.keys() \
            if x not in self._tht_ttvt_maker.ttvt_dict.keys()
        ]

        item = {
            SC.K_TO_HA_TANG: "Chưa gán CSHT nên chưa có ĐVQL",
            SC.K_TTVT: "",
            SC.K_3G: 0,
            SC.K_4G: 0,
            SC.K_5G: 0,
        }

        for x in unknown_ttvt:
            item[SC.K_3G] = self._bts_counter_by_ttvt_dict[x][T.HeThong._3G.value]
            item[SC.K_4G] = self._bts_counter_by_ttvt_dict[x][T.HeThong._4G.value]
            item[SC.K_5G] = self._bts_counter_by_ttvt_dict[x][T.HeThong._5G.value]

        self._data_tghop_bts_list.append(item)

        # row tong
        item = {
            SC.K_TO_HA_TANG: "Tổng",
            SC.K_TTVT: "",
            SC.K_3G: 0,
            SC.K_4G: 0,
            SC.K_5G: 0,
        }

        for row in self._data_tghop_bts_list:
            item[SC.K_3G] += row[SC.K_3G]
            item[SC.K_4G] += row[SC.K_4G]
            item[SC.K_5G] += row[SC.K_5G]

        self._data_tghop_bts_list.append(item)
    
    def _count_info_mll_of_ttvt_x_clr(
                            self,
                            bc_chi_tiet_mll_x_item_list: list,
                            ttvt: str
    ) -> tuple[int, int]:
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
                        f'BcCbaoMllService _count_info_mll_of_ttvt_x_clr error {e}'
                    )

        return sco_mll_lan, thgian_cb_phut

    def _count_info_of_ttvt_x_nclr(
                            self,
                            ttvt: str
    ):
        ttvt = ttvt.strip().lower()

        tong_so_bts = \
            self._bts_counter_by_ttvt_dict[ttvt][T.HeThong._3G.value] \
            + self._bts_counter_by_ttvt_dict[ttvt][T.HeThong._4G.value] \
            + self._bts_counter_by_ttvt_dict[ttvt][T.HeThong._5G.value]

        mll_3g = 0
        mll_4g = 0
        mll_5g = 0
        for item in self._data_bc_cbao_mll_bts_xg_nclr_list:
            if str(item[SC.K_TTVT_2]).lower() == ttvt:
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
            if str(item[SC.K_TEN_TTVT_TRAM_VT_NETX]).lower() != ttvt:
                continue

            if str(item[SC.K_MA_LOAI_CSHT_DDONG]).lower() == 'macro':
                tg_csht_macro += 1

        csht_macro_mll = 0
        for item in self._data_bc_csht_mll_nclr_list:
            if str(item[SC.K_TTVT_2]).lower() != ttvt:
                continue

            if str(item[SC.K_UI_MA_LOAI_CSHT_DI_DONG]).lower() == 'macro':
                csht_macro_mll += 1

        return tong_so_bts, mll_3g, mll_4g, mll_5g, tong_mll, \
            tg_csht_macro, csht_macro_mll

    def _make_k_co_ne_rimsran(self, rp_al_item_dict: dict) -> None|dict:
        item = {
            SC.K_TT: to_int(rp_al_item_dict.get(SC.K_TT), force=False),
            SC.K_MUC: rp_al_item_dict.get(SC.K_MUC),
            SC.K_LOAI_NE: rp_al_item_dict.get(SC.K_LOAI_NE),
            SC.K_TEN_NE: rp_al_item_dict.get(SC.K_TEN_NE),
            SC.K_TEN_GOI_NHO: rp_al_item_dict.get(SC.K_TEN_GOI_NHO),
            SC.K_OBJECT: rp_al_item_dict.get(SC.K_OBJECT),
            SC.K_BSC_RNC: rp_al_item_dict.get(SC.K_BSC_RNC),
            SC.K_NGUYEN_NHAN: rp_al_item_dict.get(SC.K_NGUYEN_NHAN),
            SC.K_NHA_CC: rp_al_item_dict.get(SC.K_NHA_CC),
            SC.K_TG_SU_CO_1: rp_al_item_dict.get(SC.K_TG_SU_CO_1),
            SC.K_TG_CLR: rp_al_item_dict.get(SC.K_TG_CLR),
            SC.K_TG_CBAO: to_int(rp_al_item_dict.get(SC.K_TG_CBAO), force=False),
            SC.K_TTHAI_CLR: rp_al_item_dict.get(SC.K_TTHAI_CLR),
            SC.K_MA_CBAO: to_int(rp_al_item_dict.get(SC.K_MA_CBAO), force=False),
            SC.K_DETAIL: rp_al_item_dict.get(SC.K_DETAIL),
            SC.K_TINH_TP: rp_al_item_dict.get(SC.K_TINH_TP),
            SC.K_QUAN_HUYEN: rp_al_item_dict.get(SC.K_QUAN_HUYEN),
            SC.K_VNP_GHI_CHU: rp_al_item_dict.get(SC.K_VNP_GHI_CHU),
            SC.K_TINH_GHI_CHU: rp_al_item_dict.get(SC.K_TINH_GHI_CHU),
            SC.K_LOAI_SU_CO: to_int(rp_al_item_dict.get(SC.K_LOAI_SU_CO), force=False),
            SC.K_PHAN_LOAI_TRAM: rp_al_item_dict.get(SC.K_PHAN_LOAI_TRAM),
            SC.K_TIME_AC: rp_al_item_dict.get(SC.K_TIME_AC),
            SC.K_HE_THONG: rp_al_item_dict.get(SC.K_HE_THONG),
            SC.K_GLOBAL_ID: rp_al_item_dict.get(SC.K_GLOBAL_ID),
            SC.K_TGIAN_TAO_TREN_FMS: rp_al_item_dict.get(SC.K_TGIAN_TAO_TREN_FMS),
            SC.K_DVI_QLY: rp_al_item_dict.get(SC.K_DVI_QLY)
        }

        return item

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
            item[SC.K_UI_PHAN_LOAI_TRAM] = SC.K_UI_MSG_FMS_K_CO_PHLOAI_TRAM

            msg = SC.K_UI_MSG_FMS_K_CO_PHLOAI_TRAM
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
            item[SC.K_UI_TRTHAI_DAT_MNO] = SC.K_UI_MSG_KGAN_CSHT
            item[SC.K_UI_NVIEN_HTANG] = SC.K_UI_MSG_KGAN_CSHT

            return item

        try:
            item[SC.K_TTVT_2] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[item[SC.K_CSHT]][SC.K_TEN_TTVT_TRAM_VT_NETX]
            item[SC.K_UI_TO_HA_TANG] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[item[SC.K_CSHT]][SC.K_TEN_DVI_QLY]
            item[SC.K_UI_TRTHAI_DAT_MNO] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                [item[SC.K_CSHT]][SC.K_TRTHAI_DAT_MNO]

        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed csht ccl {item[SC.K_NE]} : {msg} : {e}')
            item[SC.K_TTVT_2] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_TO_HA_TANG]  = SC.K_UI_MSG_KTTHAY_CSHT
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
            msg = SC.K_UI_MSG_THT_K_KHOP
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr warning {item[SC.K_NE]} : {msg}'
            )
        else:
            if str(item[SC.K_UI_TO_HA_TANG]).lower() not in str(rp_al_item_dict[SC.K_DVI_QLY]).lower():
                msg = SC.K_UI_MSG_THT_K_KHOP
                if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
                LoggerUtil.get_logger().warning(
                    f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr warning {item[SC.K_NE]} : {msg}'
                )

        return item

    #make BC chi tiết MLL_tất cả các NN XG / make BC MLL_nguồn(trừL3_KoMPĐ)-TD
    def _make_data_bc_chi_tiet_xg_clr(self):
        for item in self._rp_al_cbao_mll_maker.rp_alarm_items_list_bts_clr:
            he_thong = item[SC.K_HE_THONG]

            _item_ret = self._make_data_bc_chi_tiet_mll_xg_item_clr(item)

            #
            if _item_ret is None:
                ret_k_co_ne_rimsran = self._make_k_co_ne_rimsran(item)
                if ret_k_co_ne_rimsran:
                    self._data_bc_cbao_mll_clr_xg_dict[he_thong].k_co_ne_rimsran.append(ret_k_co_ne_rimsran)

                continue

            #
            self._data_bc_cbao_mll_clr_xg_dict[he_thong].bc_chi_tiet_mll_tat_ca_nn_item_list.append(_item_ret)

            #
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

    def _make_bc_tghop_item_clr(
                                self,
                                he_thong,
                                bc_chi_tiet_mll_x_item_list,
                                ttvt_dict,
                                compare_row: list
    ) -> dict:
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ttvt_dict[SC.K_TO_HA_TANG]
        item[SC.K_TTVT_2] = ttvt_dict[SC.K_TTVT]

        item[SC.K_UI_TONG_SO_BTS] = self._bts_counter_by_ttvt_dict\
            [str(item[SC.K_TTVT_2]).strip().lower()]\
            [he_thong]

        item[SC.K_UI_SCO_MLL_LAN], item[SC.K_UI_TGIAN_CBAO_PHUT] = \
            self._count_info_mll_of_ttvt_x_clr(
                bc_chi_tiet_mll_x_item_list,
                item[SC.K_TTVT_2]
            )

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
                data_bc_cbao_mll_xg: DataBcCbaoMllXgStruct = \
                    self._data_bc_cbao_mll_clr_xg_dict[T.HeThong._3G.value]
            case T.HeThong._4G.value:
                data_bc_cbao_mll_xg: DataBcCbaoMllXgStruct = \
                    self._data_bc_cbao_mll_clr_xg_dict[T.HeThong._4G.value]
            case T.HeThong._5G.value:
                data_bc_cbao_mll_xg: DataBcCbaoMllXgStruct = \
                    self._data_bc_cbao_mll_clr_xg_dict[T.HeThong._5G.value]

        dynamicInfoUtil = DynamicInfoUtil()
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
            if self._site.lower() == ST.Site.ALL_SITE.value:
                pass
            elif self._site.lower() not in str(ttvt_dict[SC.K_SITE1]).lower():
                continue

            db_row_cpare = dict(compare_row_dict)
            db_row_cpare[SC.K_TTVT] = ttvt_dict[SC.K_TTVT]
            db_row_cpare: list = self._db_adapter.get_rows_list_by_value(
                SC.K_TABLE_BC_BTS_MLL_TGHOP, db_row_cpare)
            item = self._make_bc_tghop_item_clr(
                he_thong,
                data_bc_cbao_mll_xg.bc_chi_tiet_mll_tat_ca_nn_item_list,
                ttvt_dict,
                db_row_cpare
            )
            bang_tghop_mll_item_list.append(item)

            db_row_cpare = dict(compare_row_dict)
            db_row_cpare[SC.K_TTVT] = ttvt_dict[SC.K_TTVT]
            db_row_cpare: list = self._db_adapter.get_rows_list_by_value(
                SC.K_TABLE_BC_BTS_MLL_TGHOP_DA_LOAI_TRU, db_row_cpare)
            item = self._make_bc_tghop_item_clr(
                he_thong,
                data_bc_cbao_mll_xg.bc_mll_nguon_td_item_list,
                ttvt_dict,
                db_row_cpare
            )
            bang_tghop_mll_da_loai_tru_item_list.append(item)

        # sort Đơn vị quản lý -> TTVT
        try:
            bang_tghop_mll_item_list.sort(
                key=lambda x: (
                    safe_sort_value(locale.strxfrm(x.get(SC.K_UI_DON_VI_QUAN_LY))),
                    safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT_2))),
                )
            )
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcCbaoMllService _make_data_bc_tong_hop_xg_clr failed sort bang_tghop_mll_item_list: {e}'
            )

        try:
            bang_tghop_mll_da_loai_tru_item_list.sort(
                key=lambda x: (
                    safe_sort_value(locale.strxfrm(x.get(SC.K_UI_DON_VI_QUAN_LY))),
                    safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT_2))),
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
            item[SC.K_UI_PHAN_LOAI_TRAM] = SC.K_UI_MSG_FMS_K_CO_PHLOAI_TRAM

            msg = SC.K_UI_MSG_FMS_K_CO_PHLOAI_TRAM
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
        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_NE}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed'
                f' {item[SC.K_NE]} : {msg} : {e}'
            )
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
            item[SC.K_UI_TRTHAI_DAT_MNO] = self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                [item[SC.K_CSHT]][SC.K_TRTHAI_DAT_MNO]

        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                f'BcCbaoMllService _make_data_bc_chi_tiet_mll_xg_item_clr failed csht ccl {item[SC.K_NE]} : {msg} : {e}')
            item[SC.K_TTVT_2] = SC.K_UI_MSG_KTTHAY_CSHT
            item[SC.K_UI_TO_HA_TANG] = SC.K_UI_MSG_KTTHAY_CSHT
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

    def _make_data_bc_mll_bts_ttvtx_nclr(self) -> None:
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
            item[SC.K_UI_PHAN_LOAI_TRAM] = SC.K_UI_MSG_FMS_K_CO_PHLOAI_TRAM

            msg = SC.K_UI_MSG_FMS_K_CO_PHLOAI_TRAM
            if self._ui_set_error_callback: self._ui_set_error_callback(
                rp_al_item_dict.get(SC.K_TEN_NE), msg
            )
            LoggerUtil.get_logger().warning(
                f"{self.__class__.__name__} {rp_al_item_dict.get(SC.K_TEN_NE)} {msg}"
            )

        try:
            item[SC.K_UI_MA_CSHT] = self._bts_all_items_ten_tren_hthong_dict\
                [rp_al_item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT]][SC.K_MA_CSHT]
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
        for ttvt_dict in self._tht_ttvt_maker.ttvt_list:
            if self._site.lower() == ST.Site.ALL_SITE.value:
                pass
            elif self._site.lower() not in str(ttvt_dict[SC.K_SITE1]).lower():
                continue

            ret = self._make_bc_tghop_item_nclr(
                ttvt_dict
            )
            if ret != None:
                self._data_bc_tghop_nclr_list.append(ret)

        self._data_bc_tghop_nclr_list.sort(
            key=lambda x: (
                safe_sort_value(locale.strxfrm(x.get(SC.K_UI_DON_VI_QUAN_LY))),
                safe_sort_value(locale.strxfrm(x.get(SC.K_TTVT_2))),
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

        ### THONG KE BTS
        self._make_thgke_bts_chi_tiet_xg()

        self._make_thgke_tghop()

        nr3700 = sum(
            values.get("nr3700", 0)
            for values in self._bts_counter_by_ttvt_dict.values()
        )
        nr700 = sum(
            values.get("nr700", 0)
            for values in self._bts_counter_by_ttvt_dict.values()
        )
        nrkxd =  sum(
            values.get("nrkxd", 0)
            for values in self._bts_counter_by_ttvt_dict.values()
        )

        ghi_chu: str = (
            f'5G Băng tần 3700: {nr3700}\n'
            f'5G Băng tần 700: {nr700}\n'
            f'5G Băng tần "Trống": {nrkxd}\n'
        )

        ret_path = writer.write_excel_tghop_bts(
            self._data_tghop_bts_xg_dict,
            self._data_tghop_bts_list,
            ghi_chu
        )

        if self._sel_rp_type == ST.ReportTypeInfo.TGHOP_BTS.report_id.name:
            return ret_path

        ################################# MLL CLR
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

        ############################### MLL NCLR
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

class DataBcCbaoMllXgStruct:
    def __init__(self,
                bc_chi_tiet_mll_tat_ca_nn_item_list = None,
                bc_mll_nguon_td_item_list = None,
                bc_tghop_bang_tghop_mll_item_list = None,
                bc_tghop_bang_tghop_mll_da_loai_tru_item_list = None,
                k_co_ne_rimsran = None
    ):

        self.bc_chi_tiet_mll_tat_ca_nn_item_list = \
            bc_chi_tiet_mll_tat_ca_nn_item_list \
            if bc_chi_tiet_mll_tat_ca_nn_item_list is not None else []

        self.bc_mll_nguon_td_item_list = \
            bc_mll_nguon_td_item_list \
            if bc_mll_nguon_td_item_list is not None else []

        self.bc_tghop_bang_tghop_mll_item_list = \
            bc_tghop_bang_tghop_mll_item_list \
            if bc_tghop_bang_tghop_mll_item_list is not None else []

        self.bc_tghop_bang_tghop_mll_da_loai_tru_item_list = \
            bc_tghop_bang_tghop_mll_da_loai_tru_item_list \
            if bc_tghop_bang_tghop_mll_da_loai_tru_item_list is not None else []

        self.k_co_ne_rimsran = \
            k_co_ne_rimsran \
            if k_co_ne_rimsran is not None else []

class ExcelBcCbaoMllWriter:
    def __init__(self):
        self._cr_time = datetime.now(timezone(timedelta(hours=7))).strftime("%H%M%S")
        self._db_adapter = DatabaseFactory.create_adapter()
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._tht_ttvt_maker.load()

        self._site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

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
        site = self._site
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
            if (self._site.lower() != ST.Site.ALL_SITE.value) and (ret_site.lower() != self._site.lower()):
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
        match self._site.lower():
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
        chart_name = f"{he_thong} {str(chi_tieu).replace('\n', '')} {self._site}.png"
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

    def _write_data_to_excel_k_ne_rimsran_sheet(
            self, he_thong, excel_path, sheet_name, data: DataBcCbaoMllXgStruct
    ):
        HEADER = [
            SC.K_STT,
            SC.K_TT,
            SC.K_MUC,
            SC.K_LOAI_NE,
            SC.K_TEN_NE,
            SC.K_TEN_GOI_NHO,
            SC.K_OBJECT,
            SC.K_BSC_RNC,
            SC.K_NGUYEN_NHAN,
            SC.K_NHA_CC,
            SC.K_TG_SU_CO_1,
            SC.K_TG_CLR,
            SC.K_TG_CBAO,
            SC.K_TTHAI_CLR,
            SC.K_MA_CBAO,
            SC.K_DETAIL,
            SC.K_TINH_TP,
            SC.K_QUAN_HUYEN,
            SC.K_VNP_GHI_CHU,
            SC.K_TINH_GHI_CHU,
            SC.K_LOAI_SU_CO,
            SC.K_PHAN_LOAI_TRAM,
            SC.K_TIME_AC,
            SC.K_HE_THONG,
            SC.K_GLOBAL_ID,
            SC.K_TGIAN_TAO_TREN_FMS,
            SC.K_DVI_QLY,
        ]

        wb = openpyxl.load_workbook(excel_path)
        ws = wb[sheet_name]

        stt = 0
        for row_idx, item in enumerate(data.k_co_ne_rimsran, start=2):
            stt += 1

            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A") if key != SC.K_STT else stt
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER


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
            self._write_data_to_excel_k_ne_rimsran_sheet(
                he_thong,
                excel_output_path,
                "Không có NE_Rimsran",
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
        site: str = self._site
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

    def _write_excel_tghop_bts_xg(self, he_thong, ws: Worksheet, data_list):
        HEADER = []

        if he_thong in [T.HeThong._3G.value, T.HeThong._4G.value]:
            HEADER = [
                SC.K_TO_HA_TANG,
                SC.K_TTVT,

                SC.K_TRANG_THAI_HDONG,
                SC.K_MA_CSHT,
                SC.K_TEN_HE_THONG,
                SC.K_TEN_QUAN_LY,

                SC.K_TRTHAI_DAT_MNO,

                SC.K_LOAI_TRAM,
                SC.K_BG_TAN,
                SC.K_NGAY_DUYET,
                SC.K_SERVICE_IP,
                SC.K_OAM_IP,
            ]
        else:
            HEADER = [
                SC.K_TO_HA_TANG,
                SC.K_TTVT,

                SC.K_TRANG_THAI_HDONG,
                SC.K_MA_CSHT,
                SC.K_TEN_HE_THONG,
                SC.K_TEN_QUAN_LY,

                SC.K_LOAI_TRAM,
                SC.K_BG_TAN,
                SC.K_NGAY_DUYET,
                SC.K_SERVICE_IP,
                SC.K_OAM_IP,

                SC.K_IP_GW_OAM,
                SC.K_SERVICE_IP_GW,
                SC.K_SERVICE_VLAN,
                SC.K_OAM_VLAN,
            ]

        for row_idx, item in enumerate(data_list, start=2):
            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A")

                if key in [SC.K_NGAY_DUYET, SC.K_SERVICE_VLAN, SC.K_OAM_VLAN]:
                    value = to_int(value, force=False)

                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

    def _write_excel_tghop_bts(self, ws: Worksheet, data_list, ghi_chu):
        HEADER = [
            SC.K_TO_HA_TANG,
            SC.K_TTVT,
            SC.K_3G,
            SC.K_4G,
            SC.K_5G,
        ]

        RED_FONT = Font(color="FF0000")
        YELLOW_FILL = PatternFill(
            start_color="FFF2CC",
            end_color="FFF2CC",
            fill_type="solid"
        )

        ghi_chu_col_idx = 6

        last_row_idx = 2

        for row_idx, item in enumerate(data_list, start=2):
            row_kxd_ttvt = False
            row_tong_idx = False
            cells = []

            for col_idx, key in enumerate(HEADER, start=1):
                value = item.get(key, "N/A")

                cell = ws.cell(
                    row=row_idx,
                    column=col_idx,
                    value=value
                )
                cell.border = T.EX_FORMAT_THIN_BORDER
                cells.append(cell)

                value_lower = str(value).lower()

                if 'đvql' in value_lower:
                    row_kxd_ttvt = True
                elif value_lower == 'tổng':
                    row_tong_idx = True

            if row_kxd_ttvt:
                for cell in cells:
                    cell.font = RED_FONT

            elif row_tong_idx:
                for col_idx in range(1, ghi_chu_col_idx+1):
                    cell = ws.cell(
                        row=row_idx,
                        column=col_idx
                    )
                    cell.fill = YELLOW_FILL
                    cell.font = Font( # Bold
                        bold=True
                    )

            last_row_idx = row_idx

        ### Ghi chu
        ws.merge_cells(
            start_row=2,
            end_row=last_row_idx-1,
            start_column=ghi_chu_col_idx,
            end_column=ghi_chu_col_idx
        )

        # Set value vào ô đầu tiên của merged range
        cell = ws.cell(row=2, column=ghi_chu_col_idx)
        cell.value = str(ghi_chu)

        # Center + Wrap Text
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )

        # Apply border cho merged range
        for row in ws.iter_rows(
            min_row=2,
            max_row=last_row_idx,
            min_col=ghi_chu_col_idx,
            max_col=ghi_chu_col_idx
        ):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER

    def write_excel_tghop_bts(
                            self,
                            data_tghop_bts_chtiet_xg_dict: dict,
                            data_tghop_bts_list: list,
                            ghi_chu: str
                        ) -> None|str:
        site: str = self._site
        if site.lower() == ST.Site.ALL_SITE.value:
            site = "2Site"

        excel_output_template_path = \
                    ExplorerUtil().get_output_template_file_path("Tổng hợp BTS-template.xlsx")

        excel_bc_cbao_mll_xg_name = \
            "Tổng hợp BTS" + \
            f"_{site}" + \
            f"_{self._cr_time}" + \
            ".xlsx"

        excel_path = os.path.join(
            self._output_folder_path, excel_bc_cbao_mll_xg_name
        )

        shutil.copy(
            excel_output_template_path, excel_path
        )

        #
        try:
            wb = openpyxl.load_workbook(excel_path)

            for he_thong in [T.HeThong._3G.value, T.HeThong._4G.value, T.HeThong._5G.value]:
                ws = wb[str(he_thong)]
                self._write_excel_tghop_bts_xg(he_thong, ws, data_tghop_bts_chtiet_xg_dict[he_thong])

            #
            ws = wb["TONGHOP"]
            self._write_excel_tghop_bts(ws, data_tghop_bts_list, ghi_chu)

        except Exception as e:
            LoggerUtil.get_logger().error(
                f"QlyHsuatGponService export_to_excel tghop_bts failed: {e}"
            )
            raise RuntimeError
        finally:
            try:
                wb.save(excel_path)
                wb.close()
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'QlyHsuatGponService: unable to close workbook tghop_bts: {e}'
                )
                raise RuntimeError

        return self._output_folder_path

class ExcelDsachLoiWriter:
    def __init__(self):
        pass

    def write_excel(self, data: list) -> str:
        return self._write_excel_dsach_loi(data)

    def _write_data_to_excel_by_header(self,
                                       sheet_opened: Worksheet,
                                       row_index: int,
                                       header_dict: dict,
                                       data_dict: dict,
    ):
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

    def _write_excel_dsach_loi(self, data: list[dict]) -> str:
        excel_path = self._create_dsach_loi_output()

        # sort data by priority
        error_list_dict_by_key = defaultdict(list)
        error_list: list[dict] = []

        cbao_priority = {
            SC.K_UI_MSG_KTTHAY_NE: 1,
            SC.K_UI_MSG_FMS_K_CO_PHLOAI_TRAM: 2,
            SC.K_UI_MSG_KGAN_CSHT: 3,
            SC.K_UI_MSG_KTTHAY_CSHT: 4,
            SC.K_UI_MSG_KTTHAY_DAU_MOI_CSHT: 5,
            SC.K_UI_MSG_NOT_DETECT_SITE: 6,
            SC.K_UI_MSG_THT_K_KHOP: 7,
            SC.K_UI_MSG_MISS_DB: 8,
        }

        for item in data:
            key = item.get(SC.K_UI_ERROR, None)
            des = item.get(SC.K_UI_DESCRIPTION, None)

            error_list_dict_by_key[key].append(des)

        for key, val_list in error_list_dict_by_key.items():
            val_list.sort(
                key=lambda x: safe_sort_num(cbao_priority.get(x))
            )
            val = ", ".join(str(val).replace("CB: ", "") for val in val_list)

            error_list.append({
                SC.K_UI_ERROR: key,
                SC.K_UI_DESCRIPTION: val
            })

        error_list.sort(
            key=lambda x: safe_sort_value(locale.strxfrm(x.get(SC.K_UI_ERROR)))
        )

        #
        wb = openpyxl.load_workbook(excel_path)
        sheet = wb[SC.K_SHEET_DSACH_LOI]
        header_dict = {
            SC.K_UI_ERROR: 2,
            SC.K_UI_DESCRIPTION: 3,
        }
        start_row = 2
        for item in error_list:
            start_row += 1
            self._write_data_to_excel_by_header(sheet, start_row, header_dict, item)

        wb.save(excel_path)
        wb.close()

        return excel_path