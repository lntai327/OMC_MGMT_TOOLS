from share.constant import constant as SC
from backend.constant import type as T
from backend.util.database_util import DatabaseFactory

class CFBtsMaker():
    def __init__(self):
        self._db_adapter = DatabaseFactory.create_adapter()
        self.ng_nhan_mll_site_list = []
        self.ng_nhan_mat_nguon_ac_list = []

    def load(self):
        self.load_items_list_from_db()

    def load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(SC.K_TABLE_NG_NHAN)
        loaded_items = list(loaded_items) if loaded_items else []

        for item in loaded_items:
            if item['mll_site'] == 1:
                self.ng_nhan_mll_site_list.append(item)
            if item['mat_nguon_ac'] == 1:
                self.ng_nhan_mat_nguon_ac_list.append(item)