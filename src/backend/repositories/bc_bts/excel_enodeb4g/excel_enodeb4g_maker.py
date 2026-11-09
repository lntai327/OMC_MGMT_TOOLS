from share.constant import constant as SC
from backend.repositories.bc_bts.excel_enodeb4g.excel_enodeb4g_loader import *
from backend.util.database_util import DatabaseFactory

class ExcelEnodeb4gSheetMaker():
    def __init__(self):
        self._db_adapter = DatabaseFactory.create_adapter()
        self.enodeb4g_items_list_all = []

    def load(self):
        self._load_items_list_from_db()
        self._normalize()

    def _normalize(self):
        pass

    def update_db(self):
        self._loadFromExcel()
        self._write_to_db()

    def _loadFromExcel(self):
        # load items
        items_list_all = ExcelEnodeb4gLoader().load_items()
        items_list_all = [item.to_dict() for item in items_list_all]
        self.enodeb4g_items_list_all = list(
            item for item in items_list_all \
            if str(item[SC.K_TRANG_THAI_HDONG]).lower() == "onair" #nomalize data
        )

    def _write_to_db(self):
        self._db_adapter.write_to_db(SC.K_TABLE_ENODEB4G, self.enodeb4g_items_list_all)

    def _load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(SC.K_TABLE_ENODEB4G)
        for item in loaded_items:
            ten_hthong = str(item[SC.K_TEN_TREN_HE_THONG])

            item[SC.K_TEN_TREN_HE_THONG_COMPACT] = (
                ten_hthong[2:].replace("-", "")
                if ten_hthong
                else ""
            )

        self.enodeb4g_items_list_all = list(loaded_items) if loaded_items else []