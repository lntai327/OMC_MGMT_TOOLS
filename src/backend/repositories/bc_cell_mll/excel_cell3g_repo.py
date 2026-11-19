from backend.constant import type as T
from backend.util.database_util import DatabaseFactory
from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.constant import constant as SC

class Cell3gSheet:
    def __init__(self):
        self.trthai_hdong = None
        self.ten_tren_he_thong = None
        self.ma_csht_cua_cell = None
        self.ma_csht_cua_tram = None
        self.dia_chi = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TRANG_THAI_HDONG: self.trthai_hdong,
            SC.K_TEN_TREN_HE_THONG: self.ten_tren_he_thong,
            SC.K_MA_CSHT_CUA_CELL: self.ma_csht_cua_cell, 
            SC.K_MA_CSHT_CUA_TRAM: self.ma_csht_cua_tram,
            SC.K_DIA_CHI: self.dia_chi,
        }

    def load(self, item_dic):
        self.trthai_hdong = item_dic.get(SC.K_UI_TRANG_THAI_HDONG)
        self.ten_tren_he_thong = item_dic.get(SC.K_UI_TEN_TREN_HE_THONG)
        self.ma_csht_cua_cell = item_dic.get(SC.K_UI_MA_CSHT_CUA_CELL)
        self.ma_csht_cua_tram = item_dic.get(SC.K_UI_MA_CSHT_CUA_TRAM)
        self.dia_chi = item_dic.get(SC.K_UI_DIA_CHI)

        return self

class ExcelCell3gLoader:
    def __init__(self):
        pass

    def load_cell3g_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_CELL3G_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_CELL3G_KEY, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_CELL3G_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_CELL3G_KEY,
                excel_info_key=SC.K_EXCEL_CELL3G_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [Cell3gSheet().load(x) for x in all_items_in_sheet_list]

class ExcelCell3gService():
    def __init__(self):
        self._db_adapter = DatabaseFactory.create_adapter()
        self.cell3g_items_list_all = []

    def load(self):
        self._load_items_list_from_db()

    def update_db(self):
        self._loadFromExcel()
        self._write_to_db()

    def _loadFromExcel(self):
        # load items
        items_list_latest_all = ExcelCell3gLoader().load_cell3g_items()
        items_list_latest_all = [item.to_dict() for item in items_list_latest_all]
        self.cell3g_items_list_all = list(
            item for item in items_list_latest_all \
            if str(item[SC.K_TRANG_THAI_HDONG]).strip().lower() == "onair" #normalize data
        )

    def _write_to_db(self):

        self._db_adapter.write_to_db(SC.K_TABLE_CELL3G, self.cell3g_items_list_all)

    def _load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(SC.K_TABLE_CELL3G)

        for item in loaded_items:
            item[SC.K_LOAI_DOI_TUONG] = T.LoaiNE.CELL3G.name

        self.cell3g_items_list_all = list(loaded_items) if loaded_items else []