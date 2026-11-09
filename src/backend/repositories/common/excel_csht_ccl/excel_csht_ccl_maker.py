# from collections import defaultdict
# import os

from share.constant import constant as SC
# from constant import type as T
from backend.repositories.common.excel_csht_ccl.excel_csht_ccl_loader import *
# from util.logger_util import LoggerUtil
from backend.util.database_util import DatabaseFactory

class ExcelCshtCclMaker():
    def __init__(self):
        self._db_adapter = DatabaseFactory.create_adapter()
        self.csht_mdsd_items_list_all = []

        self.csht_mdsd_items_ma_csht_dict = {}

    def load(self):
        self._load_items_list_from_db()
        self._prepare_data()

    def _prepare_data(self):
        for item in self.csht_mdsd_items_list_all:
            self.csht_mdsd_items_ma_csht_dict[item[SC.K_MA_CSHT]] = item

    def update_db(self):
        self._loadFromExcel()
        self._write_to_db()

    def _loadFromExcel(self):
        _csht_mdsd_items_list_all = ExcelCshtCclLoader().load_items()
        self.csht_mdsd_items_list_all =\
            [item for item in _csht_mdsd_items_list_all if \
            str(item[SC.K_TRANG_THAI]).lower() == "đang hoạt động"]

    def _write_to_db(self):
        list_of_dicts = [item.to_dict() for item in self.csht_mdsd_items_list_all]
        self._db_adapter.write_to_db(SC.K_TABLE_CSHT_CCL, list_of_dicts)

    def _load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(SC.K_TABLE_CSHT_CCL)
        self.csht_mdsd_items_list_all = list(loaded_items) if loaded_items else []