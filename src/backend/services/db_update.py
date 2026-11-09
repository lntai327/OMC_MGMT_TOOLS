from backend.repositories.bc_cell_mll.excel_cell3g.excel_cell3g_maker import ExcelCell3gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell4g.excel_cell4g_maker import ExcelCell4gSheetMaker
from backend.repositories.bc_cell_mll.excel_cell5g.excel_cell5g_maker import ExcelCell5gSheetMaker

from backend.repositories.bc_bts.excel_nodeb3g.excel_nodeb3g_maker import ExcelNodeb3gSheetMaker
from backend.repositories.bc_bts.excel_enodeb4g.excel_enodeb4g_maker import ExcelEnodeb4gSheetMaker
from backend.repositories.bc_bts.excel_gnodeb5g.excel_gnodeb5g_maker import ExcelGnodeb5gSheetMaker
from backend.repositories.bc_bts.excel_dmoi_qly_csht.excel_dmoi_qly_csht_maker import ExcelDmoiQlyCshtMaker

from backend.repositories.pon.pon_rp_card_access_repo import RpCardAccessService
from backend.repositories.pon.pon_rp_trans_access_repo import RpTransAccessService
from backend.repositories.pon.pon_thbi_access_repo import ThbiAccessService
from backend.repositories.pon.pon_bc_chi_tiet_onu_repo import BcChTietOnuService
from backend.repositories.pon.pon_ds_tbao_xgspon_dong_repo import DsTbaoXgsponDongService
from backend.repositories.pon.pon_ds_tbao_xgspon_tay_repo import DsTbaoXgsponTayService
from backend.repositories.pon.pon_tbao_fiber_theo_visa_dong_repo import TbaoFiberVisaDongService
from backend.repositories.pon.pon_tbao_fiber_theo_visa_tay_repo import TbaoFiberVisaTayService

from backend.repositories.megawan_metronet.megawan_metronet_repo import MegawanService

from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker

from share.constant import constant as SC
from share.util.logger_util import LoggerUtil

class DbUpdate:
    def __init__(self):
        pass

    def update_db(self, excel_info_key):
        LoggerUtil.get_logger().info(f'DbUpdate update_db start {excel_info_key}')
        match excel_info_key:
            #
            case SC.K_EXCEL_CSHT_CCL_KEY:
                CshtCclService().import_from_excel()
            case SC.K_EXCEL_THT_TTVT_KEY:
                ExcelThtTtvtMaker().update_db()

            #
            case SC.K_EXCEL_CELL3G_KEY:
                ExcelCell3gSheetMaker().update_db()
            case SC.K_EXCEL_CELL4G_KEY:
                ExcelCell4gSheetMaker().update_db()
            case SC.K_EXCEL_CELL5G_KEY:
                ExcelCell5gSheetMaker().update_db()

            #
            case SC.K_EXCEL_NODEB3G_KEY:
                ExcelNodeb3gSheetMaker().update_db()
            case SC.K_EXCEL_ENODEB4G_KEY:
                ExcelEnodeb4gSheetMaker().update_db()
            case SC.K_EXCEL_GNODEB5G_KEY:
                ExcelGnodeb5gSheetMaker().update_db()
            case SC.K_EXCEL_DMOI_QLY_CSHT_KEY | SC.K_EXCEL_DMOI_QLY_CSHT_KEY_1:
                ExcelDmoiQlyCshtMaker().update_db()

            #
            case SC.K_EXCEL_RP_CARD_BY_UNIT:
                RpCardAccessService().import_from_excel()
            case SC.K_EXCEL_RP_TRANS_BY_UNIT:
                RpTransAccessService().import_from_excel()
            case SC.K_EXCEL_THBI_ACCESS:
                ThbiAccessService().import_from_excel()
            case SC.K_EXCEL_BC_CHTIET_ONU:
                BcChTietOnuService().import_from_excel()
            case SC.K_EXCEL_TBAO_FIBER_VISA_DONG:
                TbaoFiberVisaDongService().import_from_excel()
            case SC.K_EXCEL_TBAO_FIBER_VISA_TAY:
                TbaoFiberVisaTayService().import_from_excel()
            case SC.K_EXCEL_DS_THBAO_XGSPON_DONG:
                DsTbaoXgsponDongService().import_from_excel()
            case SC.K_EXCEL_DS_THBAO_XGSPON_TAY:
                DsTbaoXgsponTayService().import_from_excel()

            # Megawan
            case SC.K_EXCEL_MEGAWAN:
                MegawanService().import_from_excel()

            #
            case _:
                LoggerUtil.get_logger().error(
                    f'DbUpdate update_db unknow {excel_info_key}'
                )
                return False
        LoggerUtil.get_logger().info(f'DbUpdate update_db end {excel_info_key}')
        return True