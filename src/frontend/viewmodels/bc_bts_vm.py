"""BcBtsViewModel — state and business logic for the BcBts report page."""
import threading
from typing import Callable

from backend.services.bc_chay_mpd_qua_bgs_service import BcChayMpdQuaBgsService
from backend.services.bc_cbao_mll_service import BcCbaoMllService, ExcelDsachLoiWriter
from frontend.viewmodels.base_vm import BaseViewModel
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.time_util import TimeUtil
from share.constant import type as ST
from share.constant import constant as SC

class BcBtsViewModel(BaseViewModel):
    """ViewModel for the BcBts page.

    Observable keys:
        "is_loading"              — bool
        "alarm_report_path"       — str
        "rp_nclr_cpare_path"      — str
        "file_report_result_path" — str
        "report_src_data"         — str
        "errors"                  — list of {LỖI, MÔ TẢ} dicts
    """

    def __init__(self):
        super().__init__()
        dynamic_info = DynamicInfoUtil()

        self._is_loading: bool = False
        self._alarm_report_path: str = SC.K_EMPTY
        self._rp_nclr_cpare_path: str = SC.K_EMPTY
        self._file_report_result_path: str = SC.K_EMPTY
        self._report_src_data: str = dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_SRC_DATA) or ""
        self._tgian_cb: str = dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_TGIAN_CBAO_KEY) or ""
        self._sel_rp_type: str = dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_REPORT_TYPE) or ""
        self._rp_time_cpare_number: str = dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE_NUMBER) or ""
        self._loai_dmoi_qly: str = dynamic_info.get_value(2, SC.K_SCREEN_INPUT, "loai_dmoi_qly_csht") or "0"
        self._save_ret_bc_mll_to_db: bool = bool(
            int(dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_SAVE_BC_THOP_TO_DB) or 0)
        )
        self._errors: list[dict] = []
        self._selected_file_dict: dict = {}

        self._dynamic_info_util = DynamicInfoUtil()
        self._explorer_util = ExplorerUtil()
        self._bc_chay_mpd_qua_bgs_maker = BcChayMpdQuaBgsService(self._on_maker_error)
        self._bc_cbao_mll_maker = BcCbaoMllService(self._on_maker_error)

        # reset compare selection
        self._dynamic_info_util.set_value("0", 2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT)

    # ------------------------------------------------------------------ #
    # Observable properties
    # ------------------------------------------------------------------ #

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @is_loading.setter
    def is_loading(self, v: bool):
        self._is_loading = v
        self.notify("is_loading")

    @property
    def alarm_report_path(self) -> str:
        return self._alarm_report_path

    @alarm_report_path.setter
    def alarm_report_path(self, v: str):
        self._alarm_report_path = v
        self.notify("alarm_report_path")

    @property
    def rp_nclr_cpare_path(self) -> str:
        return self._rp_nclr_cpare_path

    @rp_nclr_cpare_path.setter
    def rp_nclr_cpare_path(self, v: str):
        self._rp_nclr_cpare_path = v
        self._on_rp_cpare_path_changed(v)
        self.notify("rp_nclr_cpare_path")

    @property
    def file_report_result_path(self) -> str:
        return self._file_report_result_path

    @file_report_result_path.setter
    def file_report_result_path(self, v: str):
        self._file_report_result_path = v
        self.notify("file_report_result_path")

    @property
    def report_src_data(self) -> str:
        return self._report_src_data

    @report_src_data.setter
    def report_src_data(self, v: str):
        self._report_src_data = v

    @property
    def tgian_cb(self) -> str:
        return self._tgian_cb

    @tgian_cb.setter
    def tgian_cb(self, v: str):
        self._tgian_cb = v
        self._dynamic_info_util.set_value(v, 2, SC.K_SCREEN_INPUT, SC.K_TGIAN_CBAO_KEY)

    @property
    def sel_rp_type(self) -> str:
        return self._sel_rp_type

    @sel_rp_type.setter
    def sel_rp_type(self, v: str):
        self._sel_rp_type = v
        self._dynamic_info_util.set_value(v, 2, SC.K_SCREEN_INPUT, SC.K_REPORT_TYPE)

    @property
    def rp_time_cpare_number(self) -> str:
        return self._rp_time_cpare_number

    @rp_time_cpare_number.setter
    def rp_time_cpare_number(self, v: str):
        self._rp_time_cpare_number = v
        self._dynamic_info_util.set_value(
            v, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE_NUMBER
        )

    @property
    def loai_dmoi_qly(self) -> str:
        return self._loai_dmoi_qly

    @loai_dmoi_qly.setter
    def loai_dmoi_qly(self, v: str):
        self._loai_dmoi_qly = v
        self._dynamic_info_util.set_value(v, 2, SC.K_SCREEN_INPUT, "loai_dmoi_qly_csht")

    @property
    def save_ret_bc_mll_to_db(self) -> bool:
        return self._save_ret_bc_mll_to_db

    @save_ret_bc_mll_to_db.setter
    def save_ret_bc_mll_to_db(self, v: bool):
        self._save_ret_bc_mll_to_db = v
        self._dynamic_info_util.set_value(str(int(v)), 2, SC.K_SCREEN_INPUT, SC.K_SAVE_BC_THOP_TO_DB)

    @property
    def errors(self) -> list[dict]:
        return self._errors

    # ------------------------------------------------------------------ #
    # Error list
    # ------------------------------------------------------------------ #

    def add_error(self, key: str, des: str):
        item = {SC.K_UI_ERROR: key, SC.K_UI_DESCRIPTION: des}
        if item not in self._errors:
            self._errors.append(item)
            self.notify("errors")

    def clear_errors(self):
        self._errors.clear()
        self.notify("errors")

    # ------------------------------------------------------------------ #
    # File selection
    # ------------------------------------------------------------------ #

    def set_alarm_file(self, file_path: str):
        """Called by view after user picks the alarm report file."""
        import os
        if self._explorer_util.valid_sel_file(SC.K_EXCEL_RP_ALARM_KEY, file_path):
            self._selected_file_dict[SC.K_EXCEL_RP_ALARM_KEY] = file_path
            self.alarm_report_path = file_path
            self.file_report_result_path = SC.K_EMPTY
        else:
            self.notify("invalid_alarm_file")

    def clear_alarm_file(self):
        self._selected_file_dict.pop(SC.K_EXCEL_RP_ALARM_KEY, None)
        self.alarm_report_path = SC.K_EMPTY

    def set_rp_cpare_file(self, file_path: str):
        self.rp_nclr_cpare_path = file_path

    def clear_rp_cpare_file(self):
        self.rp_nclr_cpare_path = SC.K_EMPTY

    # ------------------------------------------------------------------ #
    # Internal handlers
    # ------------------------------------------------------------------ #

    def _on_rp_cpare_path_changed(self, path: str):
        import os
        if os.path.isfile(path.strip()):
            self._dynamic_info_util.set_value("1", 2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT)
            self._dynamic_info_util.set_value(path, 2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT_PATH)
        else:
            self._dynamic_info_util.set_value("0", 2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT)

    def _on_maker_error(self, key_error: str, des_error: str):
        self.add_error(key_error, des_error)

    # ------------------------------------------------------------------ #
    # Report generation
    # ------------------------------------------------------------------ #

    def get_db_update_list(self) -> list[str]:
        LoggerUtil.get_logger().info(
            f"BcBtsViewModel.get_db_update_list: sel_rp_type={self._sel_rp_type}"
        )
        match self._sel_rp_type:
            case ST.ReportTypeInfo.BC_MPD.report_id.name:
                return [
                    SC.K_EXCEL_NODEB3G_KEY,
                    SC.K_EXCEL_ENODEB4G_KEY, SC.K_EXCEL_GNODEB5G_KEY,
                    SC.K_EXCEL_THT_TTVT_KEY,
                ]
            case (ST.ReportTypeInfo.BC_CBAO_MLL.report_id.name | \
                    ST.ReportTypeInfo.TGHOP_BTS.report_id.name):
                excel_dmoi = (SC.K_EXCEL_DMOI_QLY_CSHT_KEY
                              if self._loai_dmoi_qly == "0"
                              else SC.K_EXCEL_DMOI_QLY_CSHT_KEY_1
                )

                return [
                    SC.K_EXCEL_NODEB3G_KEY,
                    SC.K_EXCEL_ENODEB4G_KEY, SC.K_EXCEL_GNODEB5G_KEY,
                    excel_dmoi, SC.K_EXCEL_CSHT_CCL_KEY,
                    SC.K_EXCEL_THT_TTVT_KEY,
                ]
            case _:
                return []

    def make_report(self) -> bool:
        ret_path = None

        self.clear_errors()
        self.file_report_result_path = SC.K_EMPTY

        if self._sel_rp_type != ST.ReportTypeInfo.TGHOP_BTS.report_id.name:
            if not self._selected_file_dict.get(SC.K_EXCEL_RP_ALARM_KEY):
                self.notify("no_alarm_file")
                return False

            try:
                if self._dynamic_info_util.update_selected_excel_info(
                        SC.K_EXCEL_RP_ALARM_KEY,
                        self._selected_file_dict[SC.K_EXCEL_RP_ALARM_KEY]
                        ) is False:
                    LoggerUtil.get_logger().error(
                        f'BcBtsViewModel make_report: required sheet not found in AL RP file: {self._selected_file_dict[SC.K_EXCEL_RP_ALARM_KEY]}'
                    )
                    self.notify("invalid_alarm_file")
                    return False

                self._explorer_util.cp_file_to_cache_by_filekey(SC.K_EXCEL_RP_ALARM_KEY)
                self._dynamic_info_util.set_value(self._report_src_data, 2, SC.K_SCREEN_INPUT, SC.K_SRC_DATA)

                if self._dynamic_info_util.get_value(2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT) == "1":
                    self._explorer_util.cp_file_to_cache_by_filekey(SC.K_EXCEL_BC_CPARE_KEY)
            except Exception as e:
                LoggerUtil.get_logger().error(f"BcBtsViewModel make_report prep error: {e}")
                return False
            finally:
                self._selected_file_dict.pop(SC.K_EXCEL_RP_ALARM_KEY, None)
                self._dynamic_info_util.set_value("0", 2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_SELECT)

        try:
            if self._sel_rp_type == ST.ReportTypeInfo.BC_MPD.report_id.name:
                ret_path = self._bc_chay_mpd_qua_bgs_maker.make_bc_chay_mpd_qua_bgs()
            elif self._sel_rp_type in (
                ST.ReportTypeInfo.BC_CBAO_MLL.report_id.name,
                ST.ReportTypeInfo.TGHOP_BTS.report_id.name
            ):
                ret_path = self._bc_cbao_mll_maker.make_bc()
            else:
                LoggerUtil.get_logger().error(f"BcBtsViewModel: unknown rp type {self._sel_rp_type}")

        except Exception as e:
            import traceback
            LoggerUtil.get_logger().error(f"BcBtsViewModel make_report error: {e}\n{traceback.format_exc()}")

        LoggerUtil.get_logger().info("BcBtsViewModel make_report done")
        return ret_path

    def on_make_report_finished(self, success: bool, ret_path: str | None = None):
        """Called on main thread after background make_report() completes."""
        if success:
            self.file_report_result_path = (
                self._dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_OUTPUT_PATH) or ""
            )
        else:
            self.file_report_result_path = SC.K_EMPTY

        # reset inputs
        self.alarm_report_path = SC.K_EMPTY
        self.rp_nclr_cpare_path = SC.K_EMPTY
        self._dynamic_info_util.set_value("0", 2, SC.K_EXCEL_BC_CPARE_KEY, SC.K_SELECT)
        src_default = "(Nguồn số liệu FMS: ...)"
        self._report_src_data = src_default
        self._dynamic_info_util.set_value(src_default, 2, SC.K_SCREEN_INPUT, SC.K_SRC_DATA)
        self.notify("report_src_data")
        self.notify("make_report_finished" if success else "make_report_failed")

    def write_excel_dsach_loi(self, data: list[dict]):
        ret_path = None

        try:
            ret_path = ExcelDsachLoiWriter().write_excel(data)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"{self.__class__.__name__} cannot export ds loi due to {e}"
            )

        return ret_path