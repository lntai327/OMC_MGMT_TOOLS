from share.constant import constant as SC
from backend.repositories.bc_bts.excel_gnodeb5g.excel_gnodeb5g_loader import *
from backend.util.database_util import DatabaseFactory

class ExcelGnodeb5gSheetMaker():
    def __init__(self):
        self._db_adapter = DatabaseFactory.create_adapter()
        self.gnodeb5g_items_list_all = []

    def load(self):
        self._load_items_list_from_db()

    # update Json file from Excel source
    def update_db(self):
        self._loadFromExcel()
        self._write_to_db()

    def _loadFromExcel(self):
        # load items
        items_list_latest_all = ExcelGnodeb5gLoader().load_items()
        items_list_latest_all = [item.to_dict() for item in items_list_latest_all]
        self.gnodeb5g_items_list_all = list(
            item for item in items_list_latest_all \
            if str(item[SC.K_TRANG_THAI_HDONG]).lower() == "onair" #nomalize data
        )

    def _write_to_db(self):
        #
        self._db_adapter.write_to_db(SC.K_TABLE_GNODEB5G, self.gnodeb5g_items_list_all)

    def _load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(SC.K_TABLE_GNODEB5G)
        for item in loaded_items:
            ten_hthong = str(item[SC.K_TEN_TREN_HE_THONG])

            item[SC.K_TEN_TREN_HE_THONG_COMPACT] = (
                ten_hthong[2:].replace("-", "")
                if ten_hthong
                else ""
            )

            item[SC.K_TEN_QUAN_LY] = SC.K_UI_MSG_MISS_DB
            item[SC.K_TRTHAI_DAT_MNO] = SC.K_UI_MSG_MISS_DB
        self.gnodeb5g_items_list_all = list(loaded_items) if loaded_items else []