from backend.repositories.bc_cell_mll.excel_cell2g.excel_cell2g_maker import ExcelCell2gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell3g.excel_cell3g_maker import ExcelCell3gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell4g.excel_cell4g_maker import ExcelCell4gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell5g.excel_cell5g_maker import ExcelCell5gSheetMaker
from backend.repositories.common.excel_csht_ccl.excel_csht_ccl_maker import ExcelCshtCclMaker
from backend.repositories.common.excel_csht_ccl.excel_csht_ccl_maker import ExcelCshtCclMaker
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker

from share.constant import constant as SC
from share.util.logger_util import LoggerUtil

class DbUpdate:
    def __init__(self):
        self._cell2g_sheet_maker_instance = ExcelCell2gSheetMaker()
        self._cell3g_sheet_maker_instance = ExcelCell3gSheetMaker()
        self._cell4g_sheet_maker_instance = ExcelCell4gSheetMaker()
        self._cell5g_sheet_maker_instance = ExcelCell5gSheetMaker()
        self._excel_csht_ccl_maker_instance = ExcelCshtCclMaker()
        self._csht_ccl_maker = ExcelCshtCclMaker()
        self._tht_ttvt_maker = ExcelThtTtvtMaker()

    def update_db(self, excel_info_key):
        LoggerUtil.get_logger().info(f'DbUpdate update_db start {excel_info_key}')
        match excel_info_key:
            #
            case SC.K_EXCEL_CSHT_CCL_KEY:
                self._excel_csht_ccl_maker_instance.update_db()
            #
            case SC.K_EXCEL_CELL2G_KEY:
                self._cell2g_sheet_maker_instance.update_db()
            case SC.K_EXCEL_CELL3G_KEY:
                self._cell3g_sheet_maker_instance.update_db()
            case SC.K_EXCEL_CELL4G_KEY:
                self._cell4g_sheet_maker_instance.update_db()
            case SC.K_EXCEL_CELL5G_KEY:
                self._cell5g_sheet_maker_instance.update_db()
            case SC.K_EXCEL_CSHT_CCL_KEY:
                self._csht_ccl_maker.update_db()
            case SC.K_EXCEL_THT_TTVT_KEY:
                self._tht_ttvt_maker.update_db()
            #
            case _:
                LoggerUtil.get_logger().error(
                    f'DbUpdate update_db unknow {excel_info_key}'
                )
                return False
        LoggerUtil.get_logger().info(f'DbUpdate update_db end {excel_info_key}')
        return True