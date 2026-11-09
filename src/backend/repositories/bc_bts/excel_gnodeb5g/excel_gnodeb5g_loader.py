import inspect

from share.constant import constant as SC
from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.constant import constant as SC

class Gnodeb5gSheet:
    def __init__(self):
        self._trang_thai_hdong = None
        self._ma_csht = None
        self._ten_tren_he_thong = None
        self._loai_tram = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TRANG_THAI_HDONG: self._trang_thai_hdong,
            SC.K_MA_CSHT: self._ma_csht,
            SC.K_TEN_TREN_HE_THONG: self._ten_tren_he_thong,
            SC.K_LOAI_TRAM: self._loai_tram
        }

    def load(self, item_dic):
        self._trang_thai_hdong = item_dic.get(SC.K_UI_TRANG_THAI_HDONG)
        self._ma_csht = item_dic.get(SC.K_UI_MA_CSHT)
        self._ten_tren_he_thong = item_dic.get(SC.K_UI_TEN_TREN_HE_THONG)
        self._loai_tram = item_dic.get(SC.K_UI_LOAI_TRAM)
        return self

class ExcelGnodeb5gLoader:
    def __init__(self):
        pass

    def load_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_GNODEB5G_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_GNODEB5G_KEY, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_GNODEB5G_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_GNODEB5G_KEY,
                excel_info_key=SC.K_EXCEL_GNODEB5G_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [Gnodeb5gSheet().load(x) for x in all_items_in_sheet_list]