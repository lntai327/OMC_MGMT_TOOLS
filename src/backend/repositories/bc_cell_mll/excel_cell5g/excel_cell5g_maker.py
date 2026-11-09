from share.constant import constant as SC
from backend.repositories.bc_cell_mll.excel_cell5g.excel_cell5g_loader import *
from backend.util.database_util import DatabaseFactory
from share.util.logger_util import LoggerUtil

class ExcelCell5gSheetMaker():
    def __init__(self):
        self._db_adapter = DatabaseFactory.create_adapter()
        self.items_list_all = []

    def load(self):
        self._load_items_list_from_db()

    def update_db(self):
        self._loadFromExcel()
        self._write_to_db()

    def _loadFromExcel(self):
        items_list_latest_all = ExcelCell5gLoader().load_items()
        self.items_list_all = list(
            item.to_dict() for item in items_list_latest_all \
            if str(item[SC.K_TRANG_THAI_HDONG]).lower() == "onair" #nomalize data
        )

    def _write_to_db(self):
        list_of_dicts = [item for item in self.items_list_all]
        self._db_adapter.write_to_db(SC.K_TABLE_CELL5G, list_of_dicts)

    def _load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(SC.K_TABLE_CELL5G)

        for item in loaded_items:
            item[SC.K_MA_CSHT_CUA_CELL] = item[SC.K_MA_CSHT] if item[SC.K_MA_CSHT] else SC.K_UI_MSG_MISS_DB
            item[SC.K_MA_CSHT_CUA_TRAM] = SC.K_UI_MSG_MISS_DB

        self.items_list_all = list(loaded_items) if loaded_items else []