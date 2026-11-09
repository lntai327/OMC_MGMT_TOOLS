import inspect

from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.constant import constant as SC

class DataSheet:
    def __init__(self):
        self._ma_csht = None
        self._ho_ten = None
        self._ten_he_thong = None
        self._don_vi = None
        self._vai_tro = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_MA_CSHT: self._ma_csht,
            SC.K_HO_TEN: self._ho_ten,
            SC.K_TEN_HE_THONG: self._ten_he_thong,
            SC.K_DVI: self._don_vi,
            SC.K_VAI_TRO: self._vai_tro
        }

    def load(self, item_dic):
        self._ma_csht = item_dic.get(SC.K_UI_MA_CSHT)
        self._ho_ten = item_dic.get("Họ và tên")
        self._ten_he_thong = item_dic.get("Tên hệ thống")
        self._don_vi = item_dic.get("Đơn vị")
        self._vai_tro = item_dic.get("Vai trò")

        return self

class ExcelDmoiQlyCshtLoader1:
    def __init__(self):
        pass

    def load_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_DMOI_QLY_CSHT_KEY_1, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_DATA, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_DMOI_QLY_CSHT_KEY_1, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_DATA,
                excel_info_key=SC.K_EXCEL_DMOI_QLY_CSHT_KEY_1,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [DataSheet().load(x) for x in all_items_in_sheet_list]