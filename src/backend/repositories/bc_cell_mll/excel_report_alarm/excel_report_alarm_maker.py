from pubsub import pub

from backend.constant import type as T
from backend.repositories.bc_cell_mll.excel_cell3g.excel_cell3g_maker import ExcelCell3gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell4g.excel_cell4g_maker import ExcelCell4gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell5g.excel_cell5g_maker import ExcelCell5gSheetMaker
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.bc_cell_mll.excel_report_alarm.excel_report_alarm_loader import *
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from share.util.logger_util import LoggerUtil

from share.constant import constant as SC
from share.constant import type as ST

class ExcelReportAlarmMaker():
    def __init__(self):
        self._cell3g_maker = ExcelCell3gSheetMaker()
        self._cell4g_maker = ExcelCell4gSheetMaker()
        self._cell5g_maker = ExcelCell5gSheetMaker()
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
            LoggerUtil.get_logger().error(f'ExcelRpAlarmMaker _normalize : exception {e}')
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
        #     f'ExcelReportAlarmMaker _normalize : report_alarm_items_list size: {len(self.report_alarm_items_list)}')
        for item in self.report_alarm_items_list[:]:
            if item in report_alarm_item_set:
                self.report_alarm_items_list.remove(item)
                # LoggerUtil.get_logger().debug(
                #     f'ExcelReportAlarmMaker _normalize  : {item}'
                #     f' is duplicated in report_alarm_items_list, removed'
                # )
                continue

            report_alarm_item_set.add(item)

            if item[SC.K_LOAI_NE] not in [T.LoaiNE.CELL3G.name,
                                         T.LoaiNE.CELL4G.name, T.LoaiNE.CELL5G.name]:
                # LoggerUtil.get_logger().debug(
                #     f'ExcelReportAlarmMaker _normalize  : {item} has invalid LoaiNE, removed'
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
                            f'ExcelReportAlarmMaker _normalize  : {item[SC.K_TEN_NE]}'
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
                    LoggerUtil.get_logger().error("ExcelReportAlarmMaker _normalize : Invalid site")
                    pass

        LoggerUtil.get_logger().info(
            f'ExcelReportAlarmMaker _normalize finished : report_alarm_items_list size: {len(self.report_alarm_items_list)}')

    def _loadFromExcel(self):
        # load items
        self.report_alarm_items_list = ExcelReportAlarmLoader().load_data_items()