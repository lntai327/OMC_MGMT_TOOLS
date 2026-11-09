from backend.repositories.bc_bts.excel_dmoi_qly_csht.excel_dmoi_qly_csht_loader import *
from backend.repositories.bc_bts.excel_dmoi_qly_csht.excel_dmoi_qly_csht_loader_1 import *
from backend.util.database_util import DatabaseFactory
from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import constant as SC

class ExcelDmoiQlyCshtMaker():
    def __init__(self):
        self.dmoi_qly_csht_items_list_all = []
        self.dmoi_qly_csht_items_ma_csht_dict = {}

        self._db_adapter = DatabaseFactory.create_adapter()

        self._loai_dmoi_qly = None
        self._excel_loader = None
        self._db_table_name = None
            
    def refresh(self):
        self._loai_dmoi_qly = DynamicInfoUtil().get_value(
            2, SC.K_SCREEN_INPUT, "loai_dmoi_qly_csht"
        )

        match self._loai_dmoi_qly:
            case "0":
                self._excel_loader = ExcelDmoiQlyCshtLoader()
                self._db_table_name = SC.K_TABLE_DMOI_QLY_CSHT
            case "1":
                self._excel_loader = ExcelDmoiQlyCshtLoader1()
                self._db_table_name = SC.K_TABLE_DMOI_QLY_CSHT_1
            case _:
                raise Exception("Invalid loai_dmoi_qly: " + self._loai_dmoi_qly)
                
    def load(self):
        self.refresh()

        self._load_items_list_from_db()
        self._prepare_data()

    def _prepare_data(self):
        self.dmoi_qly_csht_items_ma_csht_dict = {}

        for item in self.dmoi_qly_csht_items_list_all:
            self.dmoi_qly_csht_items_ma_csht_dict[item[SC.K_MA_CSHT]] = item

    def update_db(self):
        self._loadFromExcel()
        self._write_to_db()

    def _loadFromExcel(self):
        self.refresh()

        _dmoi_qly_csht_items_list_all = self._excel_loader.load_items()
        _dmoi_qly_csht_items_list_all = \
            [item.to_dict() for item in _dmoi_qly_csht_items_list_all]

        #normalize
        match self._loai_dmoi_qly:
            case "0":
                self.dmoi_qly_csht_items_list_all = \
                    [item for item in _dmoi_qly_csht_items_list_all if \
                    str(item[SC.K_PHAN_CAP]).lower() == "nhân viên hạ tầng"]
            case "1":
                self.dmoi_qly_csht_items_list_all = [
                    item for item in _dmoi_qly_csht_items_list_all
                    if (
                        str(item[SC.K_TEN_HE_THONG]).lower() == "trạm vô tuyến"
                        and str(item[SC.K_DVI]).lower() == "tổ/phòng hạ tầng"
                        and str(item[SC.K_VAI_TRO]).lower() == "main"
                    )
                ]
            case _:
                raise Exception("Invalid loai_dmoi_qly: " + self._loai_dmoi_qly)

    def _write_to_db(self):
        self._db_adapter.write_to_db(self._db_table_name, self.dmoi_qly_csht_items_list_all)

    def _load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(self._db_table_name)
        self.dmoi_qly_csht_items_list_all = list(loaded_items) if loaded_items else []