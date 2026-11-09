import inspect

from backend.util.excel_loader_util import ExcelLoaderUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil

from share.constant import constant as SC

class DataSheet:
    def __init__(self):
        self.loai_ne = None
        self.ten_ne = None
        self.tg_su_co = None
        self.nguyen_nhan = None
        self.quan_huyen = None
        self.phan_loai_tram = None

    def __getitem__(self, key):
        match key:
            case SC.K_LOAI_NE:
                return self.loai_ne
            case SC.K_TEN_NE:
                return self.ten_ne
            case SC.K_TG_SU_CO_1:
                return self.tg_su_co
            case SC.K_NGUYEN_NHAN:
                return self.nguyen_nhan
            case SC.K_QUAN_HUYEN:
                return self.quan_huyen
            case SC.K_PHAN_LOAI_TRAM:
                return self.phan_loai_tram
            case _:
                raise Exception(inspect.currentframe().f_code.co_name + "Invalid argument: " + key)

    def __setitem__(self, key, value):
        match key:
            case SC.K_TEN_NE:
                self.ten_ne = value
            case _:
                LoggerUtil.get_logger().error(f"RP AL BC CELL MLL __setitem__ Invalid argument: {key}")

    def __repr__(self):
       return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_LOAI_NE: self.loai_ne,
            SC.K_TEN_NE: self.ten_ne,
            SC.K_TG_SU_CO_1: self.tg_su_co,
            SC.K_NGUYEN_NHAN: self.nguyen_nhan,
            SC.K_QUAN_HUYEN: self.quan_huyen,
            SC.K_PHAN_LOAI_TRAM: self.phan_loai_tram,
        }

    def load(self, item_dic):
        self.loai_ne = item_dic.get(SC.K_UI_LOAI_NE)
        self.ten_ne = item_dic.get(SC.K_UI_TEN_NE)
        self.tg_su_co = item_dic.get(SC.K_UI_TG_SU_CO1)
        self.nguyen_nhan = item_dic.get(SC.K_UI_NGUYEN_NHAN1)
        self.quan_huyen = item_dic.get(SC.K_UI_QUAN_HUYEN)
        self.phan_loai_tram = item_dic.get(SC.K_UI_PHAN_LOAI_TRAM1)

        return self

class ExcelReportAlarmLoader:
    def __init__(self):
        pass

    def load_data_items(self):
        sheet_name = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_RP_ALARM_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_DATA_KEY, SC.K_NAME
        )
        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_NAME)
        )
        all_items_in_sheet_list = ExcelLoaderUtil().load_items(
            sheet_name=sheet_name,
            sheet_info_key=SC.K_SHEET_DATA_KEY,
            excel_info_key=SC.K_EXCEL_RP_AL_BC_CELL_MLL_KEY,
            excel_path=excel_path
        )
        return [DataSheet().load(x) for x in all_items_in_sheet_list]