from backend.util.database_util import DatabaseFactory
from backend.util.ex_handle_util import ExcelHandleUtil

from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import constant as SC
from share.util.explorer_util import ExplorerUtil

class DataSheet:
    def __init__(self):
        self._ma_csht = None
        self._ho_ten = None
        self._ten_he_thong = None
        self._don_vi = None
        self._vai_tro = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_MA_CSHT: self._ma_csht,
            SC.K_HO_TEN: self._ho_ten,
            SC.K_TEN_HE_THONG: self._ten_he_thong,
            SC.K_DVI: self._don_vi,
            SC.K_VAI_TRO: self._vai_tro
        }

    def load(self, item_dic):
        self._ma_csht = item_dic.get(SC.K_UI_MA_CSHT)
        self._ho_ten = item_dic.get("Họ và tên")
        self._ten_he_thong = item_dic.get("Tên hệ thống")
        self._don_vi = item_dic.get("Đơn vị")
        self._vai_tro = item_dic.get("Vai trò")

        return self

class ExcelDmoiQlyCshtLoader1:
    def __init__(self):
        pass

    def load_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_DMOI_QLY_CSHT_KEY_1, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_DATA, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_DMOI_QLY_CSHT_KEY_1, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_DATA,
                excel_info_key=SC.K_EXCEL_DMOI_QLY_CSHT_KEY_1,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [DataSheet().load(x) for x in all_items_in_sheet_list]

class DmoiQlyCshtSheet:
    def __init__(self):
        self._ma_csht = None
        self._phan_cap = None
        self._ho_ten = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_MA_CSHT: self._ma_csht,
            SC.K_PHAN_CAP: self._phan_cap,
            SC.K_HO_TEN: self._ho_ten
        }

    def load(self, item_dic):
        self._ma_csht = item_dic.get(SC.K_UI_MA_CSHT)
        self._phan_cap = item_dic.get(SC.K_UI_PHAN_CAP)
        self._ho_ten = item_dic.get(SC.K_UI_HO_TEN)

        return self

class ExcelDmoiQlyCshtLoader:
    def __init__(self):
        pass

    def load_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_DMOI_QLY_CSHT_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_DMOI_QLY_CSHT_KEY, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_DMOI_QLY_CSHT_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_DMOI_QLY_CSHT_KEY,
                excel_info_key=SC.K_EXCEL_DMOI_QLY_CSHT_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [DmoiQlyCshtSheet().load(x) for x in all_items_in_sheet_list]

class ExcelDmoiQlyCshtService():
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