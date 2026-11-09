import os
import openpyxl

from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.constant import constant as SC

class BcTgHopNclSheet:
    def __init__(self):
        self._ttvt = None
        self._tg_so_bts = None
        self._3g_mll = None
        self._4g_mll = None
        self._5g_mll = None
        self._tong_mll = None
        self._tong_csht_macro = None
        self._csht_macro_mll = None

    def __getitem__(self, key):
        match key:
            case SC.K_TTVT:
                return self._ttvt
            case SC.K_TONG_SO_BTS:
                return self._tg_so_bts
            case SC.K_3G_MLL:
                return self._3g_mll
            case SC.K_4G_MLL:
                return self._4g_mll
            case SC.K_5G_MLL:
                return self._5g_mll
            case SC.K_TONG_MLL:
                return self._tong_mll
            case SC.K_TONG_CSHT_MACRO:
                return self._tong_csht_macro
            case SC.K_CSHT_MACRO_MLL:
                return self._csht_macro_mll
            case _:
                raise Exception(f'BcTgHopNclSheet __getitem__ Invalid argument: + {key}')

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TTVT: self._ttvt,
            SC.K_TONG_SO_BTS: self._tg_so_bts,
            SC.K_3G_MLL: self._3g_mll,
            SC.K_4G_MLL: self._4g_mll,
            SC.K_5G_MLL: self._5g_mll,
            SC.K_TONG_MLL: self._tong_mll,
            SC.K_TONG_CSHT_MACRO: self._tong_csht_macro,
            SC.K_CSHT_MACRO_MLL: self._csht_macro_mll
        }

    def load(self, item_dic):
        self._ttvt = item_dic.get(2)
        self._tg_so_bts = item_dic.get(3)
        self._3g_mll = item_dic.get(4)
        self._4g_mll = item_dic.get(5)
        self._5g_mll = item_dic.get(6)
        self._tong_mll = item_dic.get(7)
        self._tong_csht_macro = item_dic.get(8)
        self._csht_macro_mll = item_dic.get(9)

        return self

class ExcellBcNclLoader:
    def __init__(self):
        pass

    def load_items(self):
        all_items_list = []
        time_cpare = ""

        file_name = os.path.basename(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT_PATH)
        )
        excel_path = ExplorerUtil().get_cache_file_path(file_name)

        wb = openpyxl.load_workbook(excel_path, data_only=True)
        sheet = wb['BÁO CÁO TỔNG HỢP']

        time_cpare = str(sheet.cell(row=2, column=3).value)
        DynamicInfoUtil().set_value(
            time_cpare, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE
        )

        #
        header_req_list = [
            1, 2, 3, 4, 5, 6, 7, 8, 9
        ]

        rows = sheet.iter_rows(min_row=11, values_only=True)
        for row in rows:
            req_colums_value_list = [row[idx] for idx in range(0, 9)]
            req_row_dic = dict(zip(header_req_list, req_colums_value_list))
            all_items_list.append(req_row_dic)

        return [BcTgHopNclSheet().load(x) for x in all_items_list]

class ExcelBcCbaoMllService():
    def __init__(self):
        self.bc_tghop_ttvt_dict = {}

    def load(self):
        self._loadFromExcel()

    def _loadFromExcel(self):
        bc_tghop_items_list = ExcellBcNclLoader().load_items()

        for item in bc_tghop_items_list:
            self.bc_tghop_ttvt_dict[item[SC.K_TTVT]] = item.to_dict()