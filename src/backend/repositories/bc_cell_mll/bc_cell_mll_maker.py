from collections import defaultdict
from pubsub import pub

from backend.constant import type as T
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.logger_util import LoggerUtil

# Fixed data
from backend.repositories.bc_cell_mll.excel_cell2g.excel_cell2g_maker import ExcelCell2gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell3g.excel_cell3g_maker import ExcelCell3gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell4g.excel_cell4g_maker import ExcelCell4gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell5g.excel_cell5g_maker import ExcelCell5gSheetMaker
from backend.repositories.common.excel_csht_ccl.excel_csht_ccl_maker import ExcelCshtCclMaker
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.repositories.bc_cell_mll.excel_bc_cell_mll.excel_bc_cell_mll_maker import ExcelBcCellMllMaker
# Input
from backend.repositories.bc_cell_mll.excel_report_alarm.excel_report_alarm_maker import ExcelReportAlarmMaker
# Output
from backend.repositories.bc_cell_mll.excel_bc_cell_mll.excel_bc_cell_mll_writer import ExcelBcCellMllWriter

from share.constant import constant as SC
from share.constant import type as ST

class BcCellMllMaker:
    def __init__(self):
        self._init_data()

        self._cell2g_sheet_maker_instance = ExcelCell2gSheetMaker()
        self._cell3g_sheet_maker_instance = ExcelCell3gSheetMaker()
        self._cell4g_sheet_maker_instance = ExcelCell4gSheetMaker()
        self._cell5g_sheet_maker_instance = ExcelCell5gSheetMaker()
        self._csht_ccl_maker = ExcelCshtCclMaker()
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self._bc_cell_mll_maker = ExcelBcCellMllMaker()

        self._excel_report_alarm_maker_instance = ExcelReportAlarmMaker()

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

        # Case 2: 2G, 3G, 4G, 5G
        _prefixes = ("2G", "3G", "4G", "5G")
        if s.startswith(_prefixes):
            return s[3:3+7]

        return None

    def _get_vi_tri_cell(self, ma_csht_cua_cell: str, ma_csht_cua_tram: str):
        if ma_csht_cua_tram == SC.K_UI_MSG_MISS_DB: #CELL5G
            return SC.K_UI_MSG_MISS_DB
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
            T.LoaiNE.CELL2G.name: 0,
            T.LoaiNE.CELL3G.name: 0,
            T.LoaiNE.CELL4G.name: 0,
            T.LoaiNE.CELL5G.name: 0,
            #TTVT
        }

        for cell in self._cellxg_item_list_latest:
            if cell[SC.K_LOAI_DOI_TUONG] not in \
                    {T.LoaiNE.CELL2G.name, T.LoaiNE.CELL3G.name,\
                    T.LoaiNE.CELL4G.name, T.LoaiNE.CELL5G.name}:
                continue

            ttvt = None
            ma_csht_cell = None
            try:
                ma_csht_cell = cell[SC.K_MA_CSHT_CUA_CELL]
                ttvt = str(self._csht_ccl_maker.csht_mdsd_items_ma_csht_dict[ma_csht_cell]\
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
                        case T.LoaiNE.CELL2G.name:
                            self._count_tong_cell_dict[T.LoaiNE.CELL2G.name] += 1
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
        self._cell2g_sheet_maker_instance.load()
        self._cell3g_sheet_maker_instance.load()
        self._cell4g_sheet_maker_instance.load()
        self._cell5g_sheet_maker_instance.load()
        self._csht_ccl_maker.load()
        self._tht_ttvt_maker.load()
        self._excel_report_alarm_maker_instance.load()

        if self._need_cpare == "1":
            self._bc_cell_mll_maker.load()

        cellxg_item_list_all = \
            self._cell5g_sheet_maker_instance.items_list_all + \
            self._cell4g_sheet_maker_instance.cell4g_items_list_all + \
            self._cell3g_sheet_maker_instance.cell3g_items_list_all + \
            self._cell2g_sheet_maker_instance.cell2g_items_list_all

        for item in cellxg_item_list_all:
            key = item[SC.K_TEN_TREN_HE_THONG]
            self._cellxg_item_ten_tren_he_thong_dict[key] = item
            key = item[SC.K_MA_CSHT_CUA_CELL]
            self._cellxg_item_ma_csht_cell_dict[key] = item

        self._cellxg_item_list_latest = \
            self._cell5g_sheet_maker_instance.items_list_all + \
            self._cell4g_sheet_maker_instance.cell4g_items_list_all + \
            self._cell3g_sheet_maker_instance.cell3g_items_list_all + \
            self._cell2g_sheet_maker_instance.cell2g_items_list_all

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
        item_mll[SC.K_UI_TEN_NE] = rp_al_item[SC.K_TEN_NE]
        item_mll[SC.K_UI_LOAI_NE] = rp_al_item[SC.K_LOAI_NE]
        item_mll[SC.K_UI_TG_SU_CO] = rp_al_item[SC.K_TG_SU_CO_1]
        item_mll[SC.K_UI_NGUYEN_NHAN2] = rp_al_item[SC.K_NGUYEN_NHAN]
        item_mll[SC.K_UI_PHAN_LOAI_TRAM] = rp_al_item[SC.K_PHAN_LOAI_TRAM]
        try:
            item_mll[SC.K_UI_MA_CSHT_CELL] = \
                self._cellxg_item_ten_tren_he_thong_dict[rp_al_item[SC.K_TEN_NE]]\
                    [SC.K_MA_CSHT_CUA_CELL]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'BcCellMllMaker _make_data_bc_chi_tiet_ttvt_x_item '
                f'{rp_al_item[SC.K_TEN_NE]} {SC.K_UI_MSG_KTTHAY_NE}'
            )
            pub.sendMessage(
                SC.K_APP_NOTI,
                noti_key=rp_al_item[SC.K_TEN_NE],
                noti_val=SC.K_UI_MSG_KTTHAY_NE,
            )
            item_mll[SC.K_UI_MA_CSHT_CELL] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_UI_TEN_GOI_NHO] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_UI_TTVT] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_UI_TO_KY_THUAT] = SC.K_UI_MSG_MISS_DB

            return item_mll

        try:
            item_mll[SC.K_UI_TEN_GOI_NHO] = \
                self._csht_ccl_maker.csht_mdsd_items_ma_csht_dict\
                    [item_mll[SC.K_UI_MA_CSHT_CELL]][SC.K_TEN_CSHT]
            item_mll[SC.K_UI_TTVT] = \
                self._csht_ccl_maker.csht_mdsd_items_ma_csht_dict\
                    [item_mll[SC.K_UI_MA_CSHT_CELL]][SC.K_TEN_TTVT_TRAM_VT_NETX]
            item_mll[SC.K_UI_TO_HA_TANG] = \
                self._csht_ccl_maker.csht_mdsd_items_ma_csht_dict\
                    [item_mll[SC.K_UI_MA_CSHT_CELL]][SC.K_TEN_DVI_QLY]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'BcCellMllMaker _make_data_bc_chi_tiet_ttvt_x_item csht ccl '
                f'{rp_al_item[SC.K_TEN_NE]} {SC.K_UI_MSG_KTTHAY_CSHT}'
            )
            pub.sendMessage(
                SC.K_APP_NOTI,
                noti_key=rp_al_item[SC.K_TEN_NE],
                noti_val=SC.K_UI_MSG_KTTHAY_CSHT,
            )
            item_mll[SC.K_UI_TEN_GOI_NHO] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_UI_TTVT] = SC.K_UI_MSG_MISS_DB
            item_mll[SC.K_UI_TO_HA_TANG] = SC.K_UI_MSG_MISS_DB

        return item_mll

    def _make_data_bc_chi_tiet_ttvt_x_items_list(self):
        for item in self._excel_report_alarm_maker_instance.report_alarm_items_list:
            item_mll = self._make_data_bc_chi_tiet_ttvt_x_item(item)
            self.bc_chi_tiet_ttvt_dict[item_mll[SC.K_UI_TTVT]]\
                .append(item_mll)

    ###########
    def _count_cellxg_hien_co_theo_ma_csht_cell_ma_tram(self, ma_csht_cell, ma_tram):
        count2g = 0
        count3g = 0
        count4g = 0
        count5g = 0

        try:
            for cell in self._cellxg_item_list_latest_ma_csht_dict_ma_tram_dict[ma_csht_cell][ma_tram]:
                match cell[SC.K_LOAI_DOI_TUONG]:
                    case T.LoaiNE.CELL2G.name:
                        count2g += 1
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
                f'BcCellMllMaker count_cellxg_hien_co_theo_ma_csht_cell_ma_tram failed {ma_csht_cell} {ma_tram}'
            )

        return count2g, count3g, count4g, count5g

    def _count_cellxg_mll_theo_ma_csht_cell_ma_tram(self, ma_csht_cell, ma_tram):
        count2g = 0
        count3g = 0
        count4g = 0
        count5g = 0

        try:
            for cell in self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict[ma_csht_cell][ma_tram]:
                match cell[SC.K_UI_LOAI_NE]:
                    case T.LoaiNE.CELL2G.name:
                        count2g += 1
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
                f'BcCellMllMaker _count_cellxg_mll_theo_ma_csht_cell_ma_tram failed {ma_csht_cell} {ma_tram}'
            )

        return count2g, count3g, count4g, count5g

    def _make_bc_th_cell_mll_theo_csht_item(self, ma_csht_cell, ma_tram):
        item = defaultdict(list)
        item[SC.K_STT] = 0
        item[SC.K_UI_MA_CSHT_CUA_CELL] = ma_csht_cell

        item[SC.K_UI_MA_TRAM] = ma_tram

        item[SC.K_UI_CELL_2G_HIEN_CO], item[SC.K_UI_CELL_3G_HIEN_CO], \
        item[SC.K_UI_CELL_4G_HIEN_CO], item[SC.K_UI_CELL_5G_HIEN_CO] = \
            self._count_cellxg_hien_co_theo_ma_csht_cell_ma_tram(ma_csht_cell, ma_tram)


        item[SC.K_UI_CELL_2G_MLL], item[SC.K_UI_CELL_3G_MLL], \
        item[SC.K_UI_CELL_4G_MLL], item[SC.K_UI_CELL_5G_MLL] = \
            self._count_cellxg_mll_theo_ma_csht_cell_ma_tram(ma_csht_cell, ma_tram)

        item[SC.K_UI_TONG_CELL] = item[SC.K_UI_CELL_2G_HIEN_CO] + \
            item[SC.K_UI_CELL_3G_HIEN_CO] + item[SC.K_UI_CELL_4G_HIEN_CO] + \
            item[SC.K_UI_CELL_5G_HIEN_CO]

        item[SC.K_UI_TONG_CELL_MLL] = item[SC.K_UI_CELL_2G_MLL] + \
            item[SC.K_UI_CELL_3G_MLL] + item[SC.K_UI_CELL_4G_MLL] + item[SC.K_UI_CELL_5G_MLL]

        try:
            item[SC.K_UI_TEN_CSHT] = self._csht_ccl_maker.csht_mdsd_items_ma_csht_dict[ma_csht_cell] \
                    [SC.K_TEN_CSHT]
            item[SC.K_UI_TTVT] = self._csht_ccl_maker.csht_mdsd_items_ma_csht_dict[ma_csht_cell]\
                [SC.K_TEN_TTVT_TRAM_VT_NETX]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'_make_bc_th_cell_mll_theo_csht_item failed csht_ccl ma_csht_cell {ma_csht_cell}')
            item[SC.K_UI_TEN_CSHT] = SC.K_UI_MSG_MISS_DB
            item[SC.K_UI_TTVT] = SC.K_UI_MSG_MISS_DB

        try:
            item[SC.K_UI_VTRI_CELL_SO_VOI_VTRI_DAT_BBU] = self._get_vi_tri_cell(
                self._cellxg_item_ma_csht_cell_dict[ma_csht_cell][SC.K_MA_CSHT_CUA_CELL],
                self._cellxg_item_ma_csht_cell_dict[ma_csht_cell][SC.K_MA_CSHT_CUA_TRAM]
            )
            item[SC.K_UI_DIA_CHI_CSHT] = self._cellxg_item_ma_csht_cell_dict[ma_csht_cell][SC.K_DIA_CHI]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                f'_make_bc_th_cell_mll_theo_csht_item failed cellxg ma_csht_cell {ma_csht_cell}')
            item[SC.K_UI_VTRI_CELL_SO_VOI_VTRI_DAT_BBU] = SC.K_UI_MSG_MISS_DB
            item[SC.K_UI_DIA_CHI_CSHT] = SC.K_UI_MSG_MISS_DB

        return item

    def _make_data_bc_th_cell_mll_theo_csht(self):
        #
        for items_list in self.bc_chi_tiet_ttvt_dict.values():
            for item in items_list:
                ma_csht_cell = item[SC.K_UI_MA_CSHT_CELL]
                ma_tram = self._extract_ma_tram_from_ten_ne(item[SC.K_UI_TEN_NE])

                if ma_csht_cell not in self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict.keys():
                    self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict[ma_csht_cell] = defaultdict(list)

                self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict[ma_csht_cell][ma_tram].append(item)

        #
        for ma_csht_cell, ma_tram_dict in self._cellxg_mll_ma_csht_cell_dict_ma_tram_dict.items():
            for ma_tram, cell_mll_list_theo_ma_tram in ma_tram_dict.items():
                bc_th_cell_mll_theo_csht_item = self._make_bc_th_cell_mll_theo_csht_item(
                    ma_csht_cell, ma_tram
                )

                self.bc_th_cell_mll_theo_csht_item_list.append(bc_th_cell_mll_theo_csht_item)

    def _make_data_bc_tghop_tong_cell_row(self):
        # Tổng cell : 2G | 3G | 4G | 5G
        tong_cell_2g = self._count_tong_cell_dict[T.LoaiNE.CELL2G.name]
        tong_cell_3g = self._count_tong_cell_dict[T.LoaiNE.CELL3G.name]
        tong_cell_4g = self._count_tong_cell_dict[T.LoaiNE.CELL4G.name]
        tong_cell_5g = self._count_tong_cell_dict[T.LoaiNE.CELL5G.name]

        #
        tong_cell_2g_mll = 0
        tong_cell_3g_mll = 0
        tong_cell_4g_mll = 0
        tong_cell_5g_mll = 0
        for item_list in self.bc_chi_tiet_ttvt_dict.values():
            for item in item_list:
                match item[SC.K_UI_LOAI_NE]:
                    case T.LoaiNE.CELL2G.name:
                        tong_cell_2g_mll += 1
                    case T.LoaiNE.CELL3G.name:
                        tong_cell_3g_mll += 1
                    case T.LoaiNE.CELL4G.name:
                        tong_cell_4g_mll += 1
                    case T.LoaiNE.CELL5G.name:
                        tong_cell_5g_mll += 1
                    case _:
                        LoggerUtil.get_logger().error(
                            f'_make_data_bc_tghop_tong_cell_row '
                            f'unknow {item[SC.K_UI_LOAI_NE]}'
                        )

        #
        tong_cell_dict = {
            1: '', #ĐƠN VỊ QUẢN LÝ
            2: SC.K_UI_TONG_CELL, #TTVT
            3: tong_cell_2g + tong_cell_3g + tong_cell_4g + tong_cell_5g, #Tổng số cell
            4: f'{tong_cell_2g_mll} / {tong_cell_2g}', #2G MLL
            5: f'{tong_cell_3g_mll} / {tong_cell_3g}', #3G MLL
            6: f'{tong_cell_4g_mll} / {tong_cell_4g}', #4G MLL
            7: f'{tong_cell_5g_mll} / {tong_cell_5g}', #5G MLL
            8: f'{
                    tong_cell_2g_mll + tong_cell_3g_mll + tong_cell_4g_mll + tong_cell_5g_mll} / {tong_cell_2g + tong_cell_3g + tong_cell_4g + tong_cell_5g
                }' #Tổng MLL
        }
        row_cpare = self._bc_cell_mll_maker.bc_tghop_ttvt_dict.get(SC.K_UI_TONG_CELL, None)
        if (self._need_cpare == "1") and isinstance(row_cpare, dict):
            tong_cell_dict[9] = row_cpare[SC.K_2G_MLL] #2G MLL
            tong_cell_dict[10] = tong_cell_2g_mll - \
                int(row_cpare[SC.K_2G_MLL].split('/')[0].strip()) #2G MLL (tăng/giảm cell)
            tong_cell_dict[11] = row_cpare[SC.K_3G_MLL] #3G MLL
            tong_cell_dict[12] = tong_cell_3g_mll - \
                int(row_cpare[SC.K_3G_MLL].split('/')[0].strip()) #3G MLL (tăng/giảm cell)
            tong_cell_dict[13] = row_cpare[SC.K_4G_MLL] #4G MLL
            tong_cell_dict[14] = tong_cell_4g_mll - \
                int(row_cpare[SC.K_4G_MLL].split('/')[0].strip()) #4G MLL (tăng/giảm cell)
            tong_cell_dict[15] = row_cpare[SC.K_5G_MLL] #5G MLL
            tong_cell_dict[16] = tong_cell_5g_mll - \
                int(row_cpare[SC.K_5G_MLL].split('/')[0].strip()) #5G MLL (tăng/giảm cell)
            tong_cell_dict[17] = row_cpare[SC.K_TONG_MLL] #Tổng MLL
        else:
            for i in range(9, 18):
                tong_cell_dict[i] = SC.K_UI_MSG_MISS_DB

        return tong_cell_dict

    def _count_xg_mll_theo_ttvt(self, ttvt: str):
        mll_2g = 0
        mll_3g = 0
        mll_4g = 0
        mll_5g = 0

        if self.bc_chi_tiet_ttvt_dict.get(ttvt) is None:
            return mll_2g, mll_3g, mll_4g, mll_5g

        for item_mll in self.bc_chi_tiet_ttvt_dict[ttvt]:
            try:
                if str(item_mll[SC.K_UI_TTVT]).lower() == ttvt.lower():
                    match item_mll[SC.K_UI_LOAI_NE]:
                        case T.LoaiNE.CELL2G.name:
                            mll_2g += 1
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
                    f'_count_xg_mll_theo_ttvt failed KeyError {item_mll[SC.K_UI_TEN_NE]} {e}')
                continue

        return mll_2g, mll_3g, mll_4g, mll_5g

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

        item[4], item[5], item[6], item[7] = \
            self._count_xg_mll_theo_ttvt(ttvt_item[SC.K_TTVT]) #2G MLL | 3G MLL | 4G MLL | 5G MLL

        item[8] = item[4] + item[5] + item[6] + item[7] #Tổng MLL

        row_cpare = self._bc_cell_mll_maker.bc_tghop_ttvt_dict.get(ttvt_item[SC.K_TTVT], None)
        if (self._need_cpare == "1") and isinstance(row_cpare, dict):
            item[9] = int(row_cpare[SC.K_2G_MLL]) #2G MLL
            item[10] = item[4] - int(row_cpare[SC.K_2G_MLL]) #2G MLL (tăng/giảm cell)
            item[11] = int(row_cpare[SC.K_3G_MLL]) #3G MLL
            item[12] = item[5] - int(row_cpare[SC.K_3G_MLL]) #3G MLL (tăng/giảm cell)
            item[13] = int(row_cpare[SC.K_4G_MLL]) #4G MLL
            item[14] = item[6] - int(row_cpare[SC.K_4G_MLL]) #4G MLL (tăng/giảm cell)
            item[15] = int(row_cpare[SC.K_5G_MLL]) #5G MLL
            item[16] = item[7] - int(row_cpare[SC.K_5G_MLL]) #5G MLL (tăng/giảm cell)
            item[17] = int(row_cpare[SC.K_TONG_MLL]) #Tổng MLL
        else:
            for i in range(9, 18):
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
        writer.write_data_to_excel_all_header_list(
            self.bc_th_cell_mll_theo_csht_item_list, SC.K_SHEET_TH_CELL_MLL_THEO_CSHT
        )

        # bc tong hop
        self._make_data_bc_tong_hop()

        writer.write_data_to_excel_bc_tong_hop_sheet(
            self.bc_tong_hop_item_list,
            SC.K_SHEET_BAO_CAO_TONG_HOP
        )