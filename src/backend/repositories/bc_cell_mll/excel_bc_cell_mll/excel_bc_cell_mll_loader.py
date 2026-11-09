import inspect
import openpyxl

from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.constant import constant as SC

class BcTgHopSheet:
    def __init__(self):
        self._ttvt = None
        self._tg_so_cell = None
        self._3g_mll = None
        self._4g_mll = None
        self._5g_mll = None
        self._tong_mll = None

    def __getitem__(self, key):
        match key:
            case SC.K_TTVT:
                return self._ttvt
            case SC.K_TONG_SO_CELL:
                return self._tg_so_cell
            case SC.K_3G_MLL:
                return self._3g_mll
            case SC.K_4G_MLL:
                return self._4g_mll
            case SC.K_5G_MLL:
                return self._5g_mll
            case SC.K_TONG_MLL:
                return self._tong_mll
            case _:
                raise Exception(inspect.currentframe().f_code.co_name + "Invalid argument: " + key)

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TTVT: self._ttvt,
            SC.K_TONG_SO_CELL: self._tg_so_cell,
            SC.K_3G_MLL: self._3g_mll,
            SC.K_4G_MLL: self._4g_mll,
            SC.K_5G_MLL: self._5g_mll,
            SC.K_TONG_MLL: self._tong_mll
        }

    def load(self, item_dic):
        self._ttvt = item_dic.get(SC.K_TTVT)
        self._tg_so_cell = item_dic.get(SC.K_UI_TONG_CELL_MLL)
        self._3g_mll = item_dic.get(SC.K_UI_3G_MLL)
        self._4g_mll = item_dic.get(SC.K_UI_4G_MLL)
        self._5g_mll = item_dic.get(SC.K_UI_5G_MLL)
        self._tong_mll = item_dic.get(SC.K_UI_TONG_MLL)

        return self

class ExcellBcCellMllLoader:
    def __init__(self):
        self._excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, SC.K_NAME)
        )

    def load_items(self):
        all_items_list = []
        time_cpare = ""

        wb = openpyxl.load_workbook(self._excel_path, data_only=True)
        sheet = wb['BÁO CÁO TỔNG HỢP']

        time_cpare = str(sheet.cell(row=5, column=4).value)
        # time_cpare = parser.parse(time_cpare).strftime(SC.K_DATETIME_FORMAT)
        DynamicInfoUtil().set_value(
            time_cpare, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE
        )

        #
        header_req_list = [
            SC.K_TTVT, SC.K_UI_TONG_CELL_MLL,
            SC.K_UI_3G_MLL, SC.K_UI_4G_MLL, SC.K_UI_5G_MLL,
            SC.K_UI_TONG_MLL
        ]

        rows = sheet.iter_rows(min_row=7, values_only=True)
        for row in rows:
            req_colums_value_list = [row[idx] if idx < len(row) else None for idx in range(1, 8)]
            req_row_dic = dict(zip(header_req_list, req_colums_value_list))
            all_items_list.append(req_row_dic)

        return [BcTgHopSheet().load(x) for x in all_items_list]