from collections import defaultdict
import locale
from openpyxl.worksheet.worksheet import Worksheet
from pubsub import pub
import os
import re
import openpyxl
import shutil
from openpyxl.styles import Font #Border, Side, Alignment, PatternFill

from backend.constant import type as T
from backend.constant import excel_struct_info as ESI
from backend.util.ex_handle_util import ExcelHandleUtil
from backend.repositories.bc_cell_mll.excel_cell3g_repo import ExcelCell3gService
from backend.repositories.bc_cell_mll.excel_cell4g_repo import ExcelCell4gService
from backend.repositories.bc_cell_mll.excel_cell5g_repo import ExcelCell5gService
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.repositories.bc_cell_mll.excel_bc_cell_mll_repo import ExcelBcCellMllService
from backend.repositories.bc_cell_mll.excel_report_alarm_repo import ExcelReportAlarmService
from backend.constant import type as T

from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.logger_util import LoggerUtil
from share.constant import constant as SC
from share.constant import type as ST
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.time_util import TimeUtil
from share.util.convert import safe_sort_num, safe_sort_value

class BcCellMllService:
    def __init__(self):
        self._init_data()

        self._cell3g_sheet_maker_instance = ExcelCell3gService()
        self._cell4g_sheet_maker_instance = ExcelCell4gService()
        self._cell5g_sheet_maker_instance = ExcelCell5gService()
        self._csht_ccl_server = CshtCclService()
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._bc_cell_mll_maker = ExcelBcCellMllService()

        self._excel_report_alarm_maker_instance = ExcelReportAlarmService()

    def _init_data(self):
        self.bc_chi_tiet_ttvt_dict = defaultdict(list)
        self.bc_th_cell_mll_theo_csht_item_list = []
        self.bc_tong_hop_item_list = []
        self.bc_tong_hop_item_list_cpare = []

        self._count_tong_cell_dict = {}
        self._cellxg_item_list_latest_ma_csht_dict_ma_tram_dict = {}
        self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict = {}
        self._cellxg_item_ten_tren_he_thong_dict = {}
        self._cellxg_item_ma_csht_cell_dict = {}

        self._need_cpare = DynamicInfoUtil().get_value(
            2, SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, SC.K_SELECT)


    #***************************Define function************************#
    # Extract "Mã trạm" from "Mã CSHT Cell"
    # vd:
    # 4G-QNN057M11-BDH -> QNN057M
    # VNP-4G-HAN031M12-BDH -> VNP-4G-HAN031M
    def _extract_ma_tram_from_ten_ne(self, s: str):
        # Case 1: VNP
        if s.startswith("VNP"):
            return s[:14]

        # Case 2: 3G, 4G, 5G
        _prefixes = ("3G", "4G", "5G")
        if s.startswith(_prefixes):
            return s[3:3+7]

        return None

    def _get_vi_tri_cell(self, ma_csht_cua_cell: str, ma_csht_cua_tram: str):
        if ma_csht_cua_cell in [SC.K_UI_MSG_MISS_DB, "", None]:
            return SC.K_KXD
        if ma_csht_cua_tram in [SC.K_UI_MSG_MISS_DB, "", None]:
            return SC.K_KXD

        elif ma_csht_cua_cell.lower() == ma_csht_cua_tram.lower():
            return SC.K_UI_CELL_TAI_TRAM
        else:
            return SC.K_UI_CELL_KHAC_TRAM

    def _count_tong_cell_hien_co(self):
        site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        if site.lower() == ST.Site.ALL_SITE.value:
            site = ""

        self._count_tong_cell_dict = {
            SC.K_UI_TONG_CELL: 0,
            T.LoaiNE.CELL3G.name: 0,
            T.LoaiNE.CELL4G.name: 0,
            T.LoaiNE.CELL5G.name: 0,
            #TTVT
        }

        for cell in self._cellxg_item_list_latest:
            ttvt = None
            ma_csht_cell = None
            try:
                ma_csht_cell = cell[SC.K_MA_CSHT_CUA_CELL]
                ttvt = str(self._csht_ccl_server.csht_mdsd_items_ma_csht_dict[ma_csht_cell]\
                    [SC.K_TEN_TTVT_TRAM_VT_NETX]).lower()
            except KeyError as e:
                LoggerUtil.get_logger().warning(
                    f'_count_tong_cell_hien_co failed {cell[SC.K_TEN_TREN_HE_THONG]}'
                    f' {SC.K_UI_MSG_KTTHAY_CSHT}'
                )
                continue

            try:
                ret_site = self._tht_ttvt_maker.ttvt_dict[ttvt][SC.K_SITE1]
                if site.lower() in ret_site.lower():
                    self._count_tong_cell_dict[SC.K_UI_TONG_CELL] += 1
                    # count theo 2|3|4|5G Hien co
                    match cell[SC.K_LOAI_DOI_TUONG]:
                        case T.LoaiNE.CELL3G.name:
                            self._count_tong_cell_dict[T.LoaiNE.CELL3G.name] += 1
                        case T.LoaiNE.CELL4G.name:
                            self._count_tong_cell_dict[T.LoaiNE.CELL4G.name] += 1
                        case T.LoaiNE.CELL5G.name:
                            self._count_tong_cell_dict[T.LoaiNE.CELL5G.name] += 1
                        case _:
                            pass

                    # count theo ttvt
                    if ttvt not in self._count_tong_cell_dict.keys():
                        self._count_tong_cell_dict[ttvt] = 1
                    else:
                        self._count_tong_cell_dict[ttvt] += 1

                    # make item list theo ma_csht_cell, ma_tram
                    ma_tram = self._extract_ma_tram_from_ten_ne(cell[SC.K_TEN_TREN_HE_THONG])
                    if ma_tram is None:
                        LoggerUtil.get_logger().error(
                            f'_count_tong_cell_hien_co failed {cell[SC.K_TEN_TREN_HE_THONG]} không xác định mã trạm'
                        )
                        continue
                    if ma_csht_cell not in self._cellxg_item_list_latest_ma_csht_dict_ma_tram_dict.keys():
                        self._cellxg_item_list_latest_ma_csht_dict_ma_tram_dict[ma_csht_cell] = defaultdict(list)
                    self._cellxg_item_list_latest_ma_csht_dict_ma_tram_dict[ma_csht_cell][ma_tram].append(cell)

            except KeyError as e:
                LoggerUtil.get_logger().warning(
                    f'_count_tong_cell_hien_co failed {cell[SC.K_TEN_TREN_HE_THONG]} {SC.K_UI_MSG_NOT_DETECT_SITE}'
                )
                continue

    def _prepare_data(self):
        self._cell3g_sheet_maker_instance.load()
        self._cell4g_sheet_maker_instance.load()
        self._cell5g_sheet_maker_instance.load()
        self._csht_ccl_server.load()
        self._tht_ttvt_maker.load()
        self._excel_report_alarm_maker_instance.load()

        if self._need_cpare == "1":
            self._bc_cell_mll_maker.load()

        cellxg_item_list_all = \
            self._cell5g_sheet_maker_instance.items_list_all + \
            self._cell4g_sheet_maker_instance.cell4g_items_list_all + \
            self._cell3g_sheet_maker_instance.cell3g_items_list_all

        for item in cellxg_item_list_all:
            try:
                key = item[SC.K_TEN_TREN_HE_THONG]
                self._cellxg_item_ten_tren_he_thong_dict[key] = item
                key = item[SC.K_MA_CSHT_CUA_CELL]
                self._cellxg_item_ma_csht_cell_dict[key] = item
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'BcCellMllService _prepare_data failed {item} as {e}'
                )
                continue

        self._cellxg_item_list_latest = \
            self._cell5g_sheet_maker_instance.items_list_all + \
            self._cell4g_sheet_maker_instance.cell4g_items_list_all + \
            self._cell3g_sheet_maker_instance.cell3g_items_list_all

        for item in self._cellxg_item_list_latest:
            self._cellxg_item_ten_tren_he_thong_dict[item[SC.K_TEN_TREN_HE_THONG]] = item
            #
            self._cellxg_item_ma_csht_cell_dict[item[SC.K_MA_CSHT_CUA_CELL]] = item

        #
        self._count_tong_cell_hien_co() # 2|3|4|5G|TTVT|list Theo ma_csht, ma_tram

    #############
    def _make_data_bc_chi_tiet_ttvt_x_item(self, rp_al_item):
        item_mll = {}
        item_mll[SC.K_STT] = 0 #later
        item_mll[SC.K_TEN_NE] = rp_al_item[SC.K_TEN_NE]
        item_mll[SC.K_LOAI_NE] = rp_al_item[SC.K_LOAI_NE]
        item_mll[SC.K_TG_SU_CO_1] = rp_al_item[SC.K_TG_SU_CO_1]
        item_mll[SC.K_NGUYEN_NHAN] = rp_al_item[SC.K_NGUYEN_NHAN]
        item_mll[SC.K_PHAN_LOAI_TRAM] = rp_al_item[SC.K_PHAN_LOAI_TRAM]
        try:
            item_mll[SC.K_MA_CSHT_CUA_CELL] = \
                self._cellxg_item_ten_tren_he_thong_dict[rp_al_item[SC.K_TEN_NE]]\
                    [SC.K_MA_CSHT_CUA_CELL]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'BcCellMllService _make_data_bc_chi_tiet_ttvt_x_item '
                f'{rp_al_item[SC.K_TEN_NE]} {SC.K_UI_MSG_KTTHAY_NE}'
            )
            pub.sendMessage(
                SC.K_APP_NOTI,
                noti_key=rp_al_item[SC.K_TEN_NE],
                noti_val=SC.K_UI_MSG_KTTHAY_NE,
            )
            item_mll[SC.K_MA_CSHT_CUA_CELL] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_TEN_CSHT] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_TTVT] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_TEN_DVI_QLY] = SC.K_UI_MSG_MISS_DB

            return item_mll

        try:
            item_mll[SC.K_TEN_CSHT] = \
                self._csht_ccl_server.csht_mdsd_items_ma_csht_dict\
                    [item_mll[SC.K_MA_CSHT_CUA_CELL]][SC.K_TEN_CSHT]
            item_mll[SC.K_TTVT] = \
                self._csht_ccl_server.csht_mdsd_items_ma_csht_dict\
                    [item_mll[SC.K_MA_CSHT_CUA_CELL]][SC.K_TEN_TTVT_TRAM_VT_NETX]
            item_mll[SC.K_TEN_DVI_QLY] = \
                self._csht_ccl_server.csht_mdsd_items_ma_csht_dict\
                    [item_mll[SC.K_MA_CSHT_CUA_CELL]][SC.K_TEN_DVI_QLY]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'BcCellMllService _make_data_bc_chi_tiet_ttvt_x_item csht ccl '
                f'{rp_al_item[SC.K_TEN_NE]} {SC.K_UI_MSG_KTTHAY_CSHT}'
            )
            pub.sendMessage(
                SC.K_APP_NOTI,
                noti_key=rp_al_item[SC.K_TEN_NE],
                noti_val=SC.K_UI_MSG_KTTHAY_CSHT,
            )
            item_mll[SC.K_TEN_CSHT] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_TTVT] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_TEN_DVI_QLY] = SC.K_UI_MSG_MISS_DB

        return item_mll

    def _make_data_bc_chi_tiet_ttvt_x_items_list(self):
        for item in self._excel_report_alarm_maker_instance.report_alarm_items_list:
            item_mll = self._make_data_bc_chi_tiet_ttvt_x_item(item)
            self.bc_chi_tiet_ttvt_dict[item_mll[SC.K_TTVT]]\
                .append(item_mll)

    ###########
    def _count_cellxg_hien_co_theo_ma_csht_cell_ma_tram(self, ma_csht_cell, ma_tram):
        count3g = 0
        count4g = 0
        count5g = 0

        try:
            for cell in self._cellxg_item_list_latest_ma_csht_dict_ma_tram_dict[ma_csht_cell][ma_tram]:
                match cell[SC.K_LOAI_DOI_TUONG]:
                    case T.LoaiNE.CELL3G.name:
                        count3g += 1
                    case T.LoaiNE.CELL4G.name:
                        count4g += 1
                    case T.LoaiNE.CELL5G.name:
                        count5g += 1
                    case _:
                        pass
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'BcCellMllService count_cellxg_hien_co_theo_ma_csht_cell_ma_tram failed {ma_csht_cell} {ma_tram}'
            )

        return count3g, count4g, count5g

    def _count_cellxg_mll_theo_ma_csht_cell_ma_tram(self, ma_csht_cell, ma_tram):
        count3g = 0
        count4g = 0
        count5g = 0

        try:
            for cell in self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict[ma_csht_cell][ma_tram]:
                match cell[SC.K_LOAI_NE]:
                    case T.LoaiNE.CELL3G.name:
                        count3g += 1
                    case T.LoaiNE.CELL4G.name:
                        count4g += 1
                    case T.LoaiNE.CELL5G.name:
                        count5g += 1
                    case _:
                        pass
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'BcCellMllService _count_cellxg_mll_theo_ma_csht_cell_ma_tram failed {ma_csht_cell} {ma_tram}'
            )

        return count3g, count4g, count5g

    def _make_bc_th_cell_mll_theo_csht_item(self, ma_csht_cell, ma_tram):
        item = defaultdict(list)
        item[SC.K_STT] = 0
        item[SC.K_MA_CSHT_CUA_CELL] = ma_csht_cell

        item[SC.K_MA_TRAM] = ma_tram

        item[SC.K_UI_CELL_3G_HIEN_CO], \
        item[SC.K_UI_CELL_4G_HIEN_CO], item[SC.K_UI_CELL_5G_HIEN_CO] = \
            self._count_cellxg_hien_co_theo_ma_csht_cell_ma_tram(ma_csht_cell, ma_tram)


        item[SC.K_UI_CELL_3G_MLL], \
        item[SC.K_UI_CELL_4G_MLL], item[SC.K_UI_CELL_5G_MLL] = \
            self._count_cellxg_mll_theo_ma_csht_cell_ma_tram(ma_csht_cell, ma_tram)

        item[SC.K_UI_TONG_CELL] = \
            item[SC.K_UI_CELL_3G_HIEN_CO] + item[SC.K_UI_CELL_4G_HIEN_CO] + \
            item[SC.K_UI_CELL_5G_HIEN_CO]

        item[SC.K_UI_TONG_CELL_MLL] = \
            item[SC.K_UI_CELL_3G_MLL] + item[SC.K_UI_CELL_4G_MLL] + item[SC.K_UI_CELL_5G_MLL]

        try:
            item[SC.K_TEN_CSHT] = self._csht_ccl_server.csht_mdsd_items_ma_csht_dict[ma_csht_cell] \
                    [SC.K_TEN_CSHT]
            item[SC.K_TTVT] = self._csht_ccl_server.csht_mdsd_items_ma_csht_dict[ma_csht_cell]\
                [SC.K_TEN_TTVT_TRAM_VT_NETX]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'_make_bc_th_cell_mll_theo_csht_item failed csht_ccl ma_csht_cell {ma_csht_cell}')
            item[SC.K_TEN_CSHT] = SC.K_UI_MSG_MISS_DB
            item[SC.K_TTVT] = SC.K_UI_MSG_MISS_DB

        try:
            item[SC.K_UI_VTRI_CELL_SO_VOI_VTRI_DAT_BBU] = self._get_vi_tri_cell(
                self._cellxg_item_ma_csht_cell_dict[ma_csht_cell][SC.K_MA_CSHT_CUA_CELL],
                self._cellxg_item_ma_csht_cell_dict[ma_csht_cell][SC.K_MA_CSHT_CUA_TRAM]
            )
            item[SC.K_DIA_CHI] = self._cellxg_item_ma_csht_cell_dict[ma_csht_cell][SC.K_DIA_CHI]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'_make_bc_th_cell_mll_theo_csht_item failed cellxg ma_csht_cell {ma_csht_cell}'
            )
            item[SC.K_UI_VTRI_CELL_SO_VOI_VTRI_DAT_BBU] = SC.K_KXD
            item[SC.K_DIA_CHI] = SC.K_UI_MSG_MISS_DB

        return item

    def _make_data_bc_th_cell_mll_theo_csht(self):
        #
        for items_list in self.bc_chi_tiet_ttvt_dict.values():
            for item in items_list:
                ma_csht_cell = item[SC.K_MA_CSHT_CUA_CELL]
                ma_tram = self._extract_ma_tram_from_ten_ne(item[SC.K_TEN_NE])

                if ma_csht_cell not in self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict.keys():
                    self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict[ma_csht_cell] = defaultdict(list)

                self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict[ma_csht_cell][ma_tram].append(item)

        #
        for ma_csht_cell, ma_tram_dict in self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict.items():
            for ma_tram, cell_mll_list_theo_ma_tram in ma_tram_dict.items():
                bc_th_cell_mll_theo_csht_item = \
                    self._make_bc_th_cell_mll_theo_csht_item(
                        ma_csht_cell, ma_tram
                    )

                self.bc_th_cell_mll_theo_csht_item_list.append(bc_th_cell_mll_theo_csht_item)

    def _make_data_bc_tghop_tong_cell_row(self):
        # Tổng cell : 3G | 4G | 5G
        tong_cell_3g = self._count_tong_cell_dict[T.LoaiNE.CELL3G.name]
        tong_cell_4g = self._count_tong_cell_dict[T.LoaiNE.CELL4G.name]
        tong_cell_5g = self._count_tong_cell_dict[T.LoaiNE.CELL5G.name]

        #
        tong_cell_3g_mll = 0
        tong_cell_4g_mll = 0
        tong_cell_5g_mll = 0
        for item_list in self.bc_chi_tiet_ttvt_dict.values():
            for item in item_list:
                match item[SC.K_LOAI_NE]:
                    case T.LoaiNE.CELL3G.name:
                        tong_cell_3g_mll += 1
                    case T.LoaiNE.CELL4G.name:
                        tong_cell_4g_mll += 1
                    case T.LoaiNE.CELL5G.name:
                        tong_cell_5g_mll += 1
                    case _:
                        LoggerUtil.get_logger().error(
                            f'_make_data_bc_tghop_tong_cell_row '
                            f'unknow {item[SC.K_LOAI_NE]}'
                        )

        #
        tong_cell_dict = {
            1: '', #ĐƠN VỊ QUẢN LÝ
            2: SC.K_UI_TONG_CELL, #TTVT
            3: tong_cell_3g + tong_cell_4g + tong_cell_5g, #Tổng số cell
            4: f'{tong_cell_3g_mll} / {tong_cell_3g}', #3G MLL
            5: f'{tong_cell_4g_mll} / {tong_cell_4g}', #4G MLL
            6: f'{tong_cell_5g_mll} / {tong_cell_5g}', #5G MLL
            7: f'{
                    tong_cell_3g_mll + tong_cell_4g_mll + tong_cell_5g_mll} / {tong_cell_3g + tong_cell_4g + tong_cell_5g
                }' #Tổng MLL
        }
        row_cpare = self._bc_cell_mll_maker.bc_tghop_ttvt_dict.get(SC.K_UI_TONG_CELL, None)
        if (self._need_cpare == "1") and isinstance(row_cpare, dict):
            tong_cell_dict[8] = row_cpare[SC.K_3G_MLL] #3G MLL
            tong_cell_dict[9] = tong_cell_3g_mll - \
                int(row_cpare[SC.K_3G_MLL].split('/')[0].strip()) #3G MLL (tăng/giảm cell)
            tong_cell_dict[10] = row_cpare[SC.K_4G_MLL] #4G MLL
            tong_cell_dict[11] = tong_cell_4g_mll - \
                int(row_cpare[SC.K_4G_MLL].split('/')[0].strip()) #4G MLL (tăng/giảm cell)
            tong_cell_dict[12] = row_cpare[SC.K_5G_MLL] #5G MLL
            tong_cell_dict[13] = tong_cell_5g_mll - \
                int(row_cpare[SC.K_5G_MLL].split('/')[0].strip()) #5G MLL (tăng/giảm cell)
            tong_cell_dict[14] = row_cpare[SC.K_TONG_MLL] #Tổng MLL
        else:
            for i in range(8, 15):
                tong_cell_dict[i] = SC.K_UI_MSG_MISS_DB

        return tong_cell_dict

    def _count_xg_mll_theo_ttvt(self, ttvt: str):
        mll_3g = 0
        mll_4g = 0
        mll_5g = 0

        if self.bc_chi_tiet_ttvt_dict.get(ttvt) is None:
            return mll_3g, mll_4g, mll_5g

        for item_mll in self.bc_chi_tiet_ttvt_dict[ttvt]:
            try:
                if str(item_mll[SC.K_TTVT]).lower() == ttvt.lower():
                    match item_mll[SC.K_LOAI_NE]:
                        case T.LoaiNE.CELL3G.name:
                            mll_3g += 1
                        case T.LoaiNE.CELL4G.name:
                            mll_4g += 1
                        case T.LoaiNE.CELL5G.name:
                            mll_5g += 1
                        case _:
                            pass
            except KeyError as e:
                LoggerUtil.get_logger().warning(
                    f'_count_xg_mll_theo_ttvt failed KeyError {item_mll[SC.K_TEN_NE]} {e}')
                continue

        return mll_3g, mll_4g, mll_5g

    def _make_data_bc_tghop_ttvt_x_item(self, ttvt_item: dict):
        #
        item = {}
        item[1] = ttvt_item[SC.K_TO_HA_TANG] #ĐƠN VỊ QUẢN LÝ: Tổ hạ tầng
        item[2] = ttvt_item[SC.K_TTVT] #TTVT

        try:
            item[3] = self._count_tong_cell_dict[str(ttvt_item[SC.K_TTVT]).lower()] #Tổng số cell
        except KeyError as e:
            LoggerUtil.get_logger().error(
                f'_make_data_bc_tghop_ttvt_x_item failed KeyError {ttvt_item[SC.K_TTVT]} {e}')
            item[3] = 0

        item[4], item[5], item[6] = \
            self._count_xg_mll_theo_ttvt(ttvt_item[SC.K_TTVT]) # 3G MLL | 4G MLL | 5G MLL

        item[7] = item[4] + item[5] + item[6] #Tổng MLL

        row_cpare = self._bc_cell_mll_maker.bc_tghop_ttvt_dict.get(ttvt_item[SC.K_TTVT], None)
        if (self._need_cpare == "1") and isinstance(row_cpare, dict):
            item[8] = int(row_cpare[SC.K_3G_MLL]) #3G MLL
            item[9] = item[4] - int(row_cpare[SC.K_3G_MLL]) #3G MLL (tăng/giảm cell)
            item[10] = int(row_cpare[SC.K_4G_MLL]) #4G MLL
            item[11] = item[5] - int(row_cpare[SC.K_4G_MLL]) #4G MLL (tăng/giảm cell)
            item[12] = int(row_cpare[SC.K_5G_MLL]) #5G MLL
            item[13] = item[6] - int(row_cpare[SC.K_5G_MLL]) #5G MLL (tăng/giảm cell)
            item[14] = int(row_cpare[SC.K_TONG_MLL]) #Tổng MLL
        else:
            for i in range(8, 15):
                item[i] = SC.K_UI_MSG_MISS_DB
        #

        return item

    def _make_data_bc_tghop_ttvt_x(self):
        site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        if site.lower() == ST.Site.ALL_SITE.value:
            site = ""

        for ttvt, ttvt_item in self._tht_ttvt_maker.ttvt_dict.items():
            if site.lower() not in ttvt_item[SC.K_SITE1].lower():
                continue

            ret = self._make_data_bc_tghop_ttvt_x_item(ttvt_item)
            if ret is not None:
                self.bc_tong_hop_item_list.append(ret)

    def _make_data_bc_tong_hop(self):
        # tong cell row
        self.bc_tong_hop_item_list.append(self._make_data_bc_tghop_tong_cell_row())
        # ttvt x row
        self._make_data_bc_tghop_ttvt_x()

    def make_bc_cell_mll(self):
        # init data
        self._init_data()
        # prepare data
        self._prepare_data()

        writer = ExcelBcCellMllWriter()

        # bc chi tiet
        self._make_data_bc_chi_tiet_ttvt_x_items_list()
        writer.write_data_to_excel_bc_ctiet_ttvt_x(
            self.bc_chi_tiet_ttvt_dict
        )

        # bc tghop theo csht
        self._make_data_bc_th_cell_mll_theo_csht()
        writer.write_data_to_th_cell_mll_theo_csht(
            self.bc_th_cell_mll_theo_csht_item_list, "TH CELL MLL theo CSHT"
        )

        # bc tong hop
        self._make_data_bc_tong_hop()

        writer.write_data_to_excel_bc_tong_hop_sheet(
            self.bc_tong_hop_item_list,
            SC.K_SHEET_BAO_CAO_TONG_HOP
        )

class ExcelBcCellMllWriter:
    def __init__(self):
        explorer_util = ExplorerUtil()
        output_folder_path = explorer_util.create_outfolder_by_rpdate()
        self.excel_output_path = os.path.join(
            output_folder_path,
            (
                f'{SC.K_EXCEL_BC_CELL_MLL_NAME}'
                f'_{
                    str(TimeUtil().get_detail_current_time_str())\
                    .replace('/', '')\
                    .replace(':', '')\
                    .replace(' ', '_') or ''
                }'
                f'.xlsx'
            )
        )
        excel_output_template_path = explorer_util.get_output_template_file_path(
            SC.K_EXCEL_BC_CELL_MLL_TEMPLATE)
        shutil.copy(excel_output_template_path, self.excel_output_path)

    def write_data_to_th_cell_mll_theo_csht(self, data_list, sheet_name):
        wb = openpyxl.load_workbook(self.excel_output_path)
        ws = wb[sheet_name]

        header_list = [
            SC.K_STT,
            SC.K_MA_CSHT_CUA_CELL,
            SC.K_UI_VTRI_CELL_SO_VOI_VTRI_DAT_BBU,
            SC.K_MA_TRAM,
            SC.K_UI_CELL_3G_HIEN_CO,
            SC.K_UI_CELL_3G_MLL,
            SC.K_UI_CELL_4G_HIEN_CO,
            SC.K_UI_CELL_4G_MLL,
            SC.K_UI_CELL_5G_HIEN_CO,
            SC.K_UI_CELL_5G_MLL,
            SC.K_UI_TONG_CELL,
            SC.K_UI_TONG_CELL_MLL,
            SC.K_TEN_CSHT,
            SC.K_DIA_CHI,
            SC.K_TTVT,
        ]

        counter = 0
        for item in data_list:
            counter += 1
            item[SC.K_STT] = counter

            row_data = [item.get(header, 'N/A') for header in header_list]
            ws.append(row_data)

        # --- set format ---
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER
                cell.font = T.EX_FORMAT_NORMAL_FONT

        wb.save(self.excel_output_path)
        wb.close()

    def write_data_to_chtiet_ttvt(self, data_list, sheet_name):
        wb = openpyxl.load_workbook(self.excel_output_path)
        ws = wb[sheet_name]

        header_list = [
            SC.K_STT,
            SC.K_MA_CSHT_CUA_CELL,
            SC.K_LOAI_NE,
            SC.K_TEN_NE,
            SC.K_TEN_CSHT,
            SC.K_TG_SU_CO_1,
            SC.K_NGUYEN_NHAN,
            SC.K_TTVT,
            SC.K_TEN_DVI_QLY,
            SC.K_PHAN_LOAI_TRAM,
        ]

        counter = 0
        for item in data_list:
            counter += 1
            item[SC.K_STT] = counter

            row_data = [item.get(header, 'N/A') for header in header_list]
            ws.append(row_data)

        # --- set format ---
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = T.EX_FORMAT_THIN_BORDER
                cell.font = T.EX_FORMAT_NORMAL_FONT

        wb.save(self.excel_output_path)
        wb.close()

    def write_data_to_excel_bc_ctiet_ttvt_x(self, data_dict: dict):
        for k, v in data_dict.items():
            if re.search("Trung tâm Viễn thông", k, re.IGNORECASE):
                sheet_name = f'Chi Tiết TTVT {k[21:].strip()}'
            else:
                sheet_name = f'Chi Tiết TTVT KXĐ'

            wb = openpyxl.load_workbook(self.excel_output_path)
            template_sheet = wb['Chi tiết TTVT X']
            ws = wb.copy_worksheet(template_sheet)
            ws.title = sheet_name
            ws.sheet_state = 'visible'
            ws.sheet_view.showGridLines = False
            wb.save(self.excel_output_path)
            wb.close()
            self.write_data_to_chtiet_ttvt(v, sheet_name)

    def write_data_to_excel_bc_tong_hop_sheet(self, data_list, sheet_name):
        dynamic_info_util = DynamicInfoUtil()
        wb = openpyxl.load_workbook(self.excel_output_path)
        ws = wb[sheet_name]

        # Report title
        site: str = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        full_site_name = ""
        match site.lower():
            case ST.Site.DONG.value:
                full_site_name = "Site Đông"
            case ST.Site.TAY.value:
                full_site_name = "Site Tây"
            case ST.Site.ALL_SITE.value:
                full_site_name = "Tất Cả Site"

        ws.cell(row=1, column= 1).value \
            = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_TITLE) +\
            f' ({full_site_name})'
        ws.cell(row=1, column= 1).font = T.EX_FORMAT_TITLE_FONT

        ws.cell(row=2, column= 1).value \
            = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SRC_DATA)
        ws.cell(row=2, column= 1).font = T.EX_FORMAT_TITLE_FONT

        # Report date
        ws.cell(row=5, column= 4).value \
            = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_DATE)
        ws.cell(row=5, column= 4).font = T.EX_FORMAT_BOLD_FONT

        # RP time cpare
        need_compare = dynamic_info_util.get_value(
            2, SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, SC.K_SELECT
        )
        if need_compare == "1":
            time_cpare = dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE)
            ws.cell(row=5, column= 8).value = time_cpare
            ws.cell(row=5, column= 8).font = T.EX_FORMAT_BOLD_FONT

        # data row
        start_row = 7
        for item in data_list:
            row_data = [item.get(header, "N/A") for header in range(1, 15)]
            ws.append(row_data)

        # --- set format ---
        for row in ws.iter_rows(min_row=start_row, max_row=ws.max_row,
                                   min_col=1, max_col=ws.max_column):
            for cell in row:
                #
                cell.border = T.EX_FORMAT_THIN_BORDER

                #
                if cell.column not in [1,2]:
                    cell.alignment = T.EX_FORMAT_ALIGNMENT_CENTER

            ttvt = row[1].value
            if ttvt and ("tổng cell" in str(ttvt).lower()) :
                for cell in row:
                    if cell.column not in [2,3]:
                        cell.font = Font(
                            bold=True, name="Times New Roman", color="FF0000"
                        )
                    else:
                        cell.font = Font(
                            bold=True, name="Times New Roman")

        wb.save(self.excel_output_path)
        wb.close()

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
            + "CELL_MLL"
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

        #
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