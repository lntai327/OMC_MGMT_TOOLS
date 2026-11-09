from share.constant import constant as SC
from backend.constant import type as T
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_loader import ExcelLoader
from backend.util.database_util import DatabaseFactory

class ExcelThtTtvtMaker():
    def __init__(self):
        self._db_adapter = DatabaseFactory.create_adapter()
        self.ttvt_list = []
        self.tht_dict = {}
        self.ttvt_dict = {}

    def load(self):
        self._load_items_list_from_db()

    def update_db(self):
        self._loadFromExcel()
        self._write_to_db()

    def _loadFromExcel(self):
        self._loader_instance = ExcelLoader()
        self.ttvt_list = self._loader_instance.load_ttvt_items()

    def _write_to_db(self):
        list_of_dicts = [item.to_dict() for item in self.ttvt_list]
        self._db_adapter.write_to_db(SC.K_TABLE_TTVT, list_of_dicts)

    def _load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(SC.K_TABLE_TTVT)
        self.ttvt_list = list(loaded_items) if loaded_items else []

        for item in self.ttvt_list:
            self.tht_dict[str(item[SC.K_TO_HA_TANG]).lower()] = item
            self.ttvt_dict[str(item[SC.K_TTVT]).lower()] = item

        #add color for TTVT
        for ttvt in self.ttvt_dict.keys():
            index = list(self.ttvt_dict.keys()).index(ttvt)
            color_index = index % len(T.RGBA_COLORS_L)
            self.ttvt_dict[ttvt][SC.K_COLOR] = T.RGBA_COLORS_L[color_index]