from pubsub import pub
import inspect

from backend.constant import type as T
from backend.repositories.bc_cell_mll.excel_cell3g_repo import ExcelCell3gService
from backend.repositories.bc_cell_mll.excel_cell4g_repo import ExcelCell4gService
from backend.repositories.bc_cell_mll.excel_cell5g_repo import ExcelCell5gService
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.logger_util import LoggerUtil
from share.constant import constant as SC
from share.constant import type as ST
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

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
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_RP_ALARM_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_DATA, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_DATA,
                excel_info_key=SC.K_EXCEL_RP_AL_BC_CELL_MLL_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [DataSheet().load(x) for x in all_items_in_sheet_list]

class ExcelReportAlarmService():
    def __init__(self):
        self._cell3g_maker = ExcelCell3gService()
        self._cell4g_maker = ExcelCell4gService()
        self._cell5g_maker = ExcelCell5gService()
        self._csht_ccl_server = CshtCclService()
        self._tht_ttvt_maker = ExcelThtTtvtMaker()
        self.loader_instance = None
        self.report_alarm_items_list = None

    def load(self):
        self._loadFromExcel()
        self._cell3g_maker.load()
        self._cell4g_maker.load()
        self._cell5g_maker.load()
        self._csht_ccl_server.load()
        self._tht_ttvt_maker.load()

        self._normalize()

    def _normalize(self):
        # Fillter condition
        site: str = ""
        try:
            dynamic_info = DynamicInfoUtil()
            site = dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        except Exception as e:
            LoggerUtil.get_logger().error(f'ExcelRpAl Cell _normalize : exception {e}')
            raise RuntimeError

        cellxg_item_list_all = \
            self._cell5g_maker.items_list_all + \
            self._cell4g_maker.cell4g_items_list_all + \
            self._cell3g_maker.cell3g_items_list_all

        cellxg_item_ten_tren_he_thong_dict = {}
        for item in cellxg_item_list_all:
            key = item[SC.K_TEN_TREN_HE_THONG]
            cellxg_item_ten_tren_he_thong_dict[key] = item

        report_alarm_item_set = set()
        # LoggerUtil.get_logger().debug(
        #     f'ExcelReportAlarmService _normalize : report_alarm_items_list size: {len(self.report_alarm_items_list)}')
        for item in self.report_alarm_items_list[:]:
            if item in report_alarm_item_set:
                self.report_alarm_items_list.remove(item)
                # LoggerUtil.get_logger().debug(
                #     f'ExcelReportAlarmService _normalize  : {item}'
                #     f' is duplicated in report_alarm_items_list, removed'
                # )
                continue

            report_alarm_item_set.add(item)

            if item[SC.K_LOAI_NE] not in [T.LoaiNE.CELL3G.name,
                                         T.LoaiNE.CELL4G.name, T.LoaiNE.CELL5G.name]:
                # LoggerUtil.get_logger().debug(
                #     f'ExcelReportAlarmService _normalize  : {item} has invalid LoaiNE, removed'
                # )
                self.report_alarm_items_list.remove(item)
                continue

            match site.lower():
                case ST.Site.ALL_SITE.value:
                    pass
                case ST.Site.DONG.value | ST.Site.TAY.value:
                    try:
                        ma_csht = cellxg_item_ten_tren_he_thong_dict[item[SC.K_TEN_NE]][SC.K_MA_CSHT_CUA_CELL]
                        ttvt = str(self._csht_ccl_server.csht_mdsd_items_ma_csht_dict\
                            [ma_csht][SC.K_TEN_TTVT_TRAM_VT_NETX]).lower()
                        if str(self._tht_ttvt_maker.ttvt_dict[ttvt][SC.K_SITE1]).lower() != \
                                str(site).lower():
                            self.report_alarm_items_list.remove(item)
                    except Exception as e:
                        LoggerUtil.get_logger().warning(
                            f'ExcelReportAlarmService _normalize  : {item[SC.K_TEN_NE]}'
                            f' {SC.K_UI_MSG_NOT_DETECT_SITE}'
                        )
                        pub.sendMessage(
                            SC.K_APP_NOTI,
                            noti_key=item[SC.K_TEN_NE],
                            noti_val=SC.K_UI_MSG_NOT_DETECT_SITE,
                        )
                        self.report_alarm_items_list.remove(item)
                    continue
                case _:
                    LoggerUtil.get_logger().error("ExcelReportAlarmService _normalize : Invalid site")
                    pass

        LoggerUtil.get_logger().info(
            f'ExcelReportAlarmService _normalize finished : report_alarm_items_list size: {len(self.report_alarm_items_list)}')

    def _loadFromExcel(self):
        # load items
        self.report_alarm_items_list = ExcelReportAlarmLoader().load_data_items()