import inspect

from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
# from util.logger_util import LoggerUtil

from share.constant import constant as SC

class TtvtSheet:
    def __init__(self):
        self._site = None
        self._ttvt = None
        self._to_ha_tang = None

    def __getitem__(self, key):
        match key:
            case SC.K_SITE1:
                return self._site
            case SC.K_TTVT:
                return self._ttvt
            case SC.K_TO_HA_TANG:
                return self._to_ha_tang
            case _:
                raise Exception(inspect.currentframe().f_code.co_name + "Invalid argument: " + key)

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_SITE1: self._site,
            SC.K_TTVT: self._ttvt,
            SC.K_TO_HA_TANG: self._to_ha_tang
        }

    def load(self, item_dic):
        self._site = item_dic[SC.K_SITE1]
        self._ttvt = item_dic[SC.K_TTVT]
        self._to_ha_tang = item_dic[SC.K_TO_HA_TANG]

        return self

class ExcelLoader:
    def __init__(self):
        pass

    def load_ttvt_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_THT_TTVT_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_TTVT_KEY, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_THT_TTVT_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_TTVT_KEY,
                excel_info_key=SC.K_EXCEL_THT_TTVT_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [TtvtSheet().load(x) for x in all_items_in_sheet_list]