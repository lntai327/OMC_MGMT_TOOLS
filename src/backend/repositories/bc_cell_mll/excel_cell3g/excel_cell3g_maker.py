from backend.repositories.bc_cell_mll.excel_cell3g.excel_cell3g_loader import *
from backend.util.database_util import DatabaseFactory

class ExcelCell3gSheetMaker():
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
        self.cell3g_items_list_all = list(
            item for item in items_list_latest_all \
            if str(item[SC.K_TRANG_THAI_HDONG]).lower() == "onair" #nomalize data
        )

    def _write_to_db(self):
        list_of_dicts = [item.to_dict() for item in self.cell3g_items_list_all]
        self._db_adapter.write_to_db(SC.K_TABLE_CELL3G, list_of_dicts)

    def _load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(SC.K_TABLE_CELL3G)
        self.cell3g_items_list_all = list(loaded_items) if loaded_items else []