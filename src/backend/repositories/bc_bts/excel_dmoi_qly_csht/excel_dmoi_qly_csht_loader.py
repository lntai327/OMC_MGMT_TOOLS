from frontend.component import explorer_ui_util
import inspect

from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.constant import constant as SC

class DmoiQlyCshtSheet:
    def __init__(self):
        self._ma_csht = None
        self._phan_cap = None
        self._ho_ten = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_MA_CSHT: self._ma_csht,
            SC.K_PHAN_CAP: self._phan_cap,
            SC.K_HO_TEN: self._ho_ten
        }

    def load(self, item_dic):
        self._ma_csht = item_dic.get(SC.K_UI_MA_CSHT)
        self._phan_cap = item_dic.get(SC.K_UI_PHAN_CAP)
        self._ho_ten = item_dic.get(SC.K_UI_HO_TEN)

        return self

class ExcelDmoiQlyCshtLoader:
    def __init__(self):
        pass

    def load_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_DMOI_QLY_CSHT_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_DMOI_QLY_CSHT_KEY, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_DMOI_QLY_CSHT_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_DMOI_QLY_CSHT_KEY,
                excel_info_key=SC.K_EXCEL_DMOI_QLY_CSHT_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [DmoiQlyCshtSheet().load(x) for x in all_items_in_sheet_list]