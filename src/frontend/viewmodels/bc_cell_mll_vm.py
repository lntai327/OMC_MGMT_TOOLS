from pubsub import pub

from backend.services.bc_cell_mll_service import BcCellMllService
from frontend.viewmodels.base_vm import BaseViewModel
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.constant import constant as SC


class BcCellMllViewModel(BaseViewModel):
    """ViewModel for the BcCellMll page.

    Observable keys:
        "is_loading"              — bool
        "alarm_report_path"       — str
        "rp_cpare_path"           — str
        "file_report_result_path" — str
        "errors"                  — list of dicts
    """

    DB_NEED_UPDATE_LIST: list[str] = [
        SC.K_EXCEL_CELL3G_KEY,
        SC.K_EXCEL_CELL4G_KEY,
        SC.K_EXCEL_CELL5G_KEY,
        SC.K_EXCEL_CSHT_CCL_KEY,
        SC.K_EXCEL_THT_TTVT_KEY,
    ]

    def __init__(self):
        super().__init__()
        pub.subscribe(self._on_maker_error, SC.K_APP_NOTI)

        self._is_loading: bool = False
        self._alarm_report_path: str = SC.K_EMPTY
        self._rp_cpare_path: str = SC.K_EMPTY
        self._file_report_result_path: str = SC.K_EMPTY
        self._report_title: str = SC.K_EXCEL_BC_CELL_MLL_TITLE
        self._report_src_data: str = DynamicInfoUtil().get_value(
            2, SC.K_SCREEN_INPUT, SC.K_SRC_DATA) or ""
        self._errors: list[dict] = []
        self._selected_file_dict: dict = {}

        self._dynamic_info_util = DynamicInfoUtil()
        self._explorer_util = ExplorerUtil()
        self._bc_cell_mll_maker = BcCellMllService()

        # reset compare selection
        self._dynamic_info_util.set_value("0", 2, SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, SC.K_SELECT)

    def destroy(self): #TO REVIEW
        try:
            pub.unsubscribe(self._on_maker_error, "PS_NOTIFY")
        except Exception:
            pass
        super().destroy()

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
    def rp_cpare_path(self) -> str:
        return self._rp_cpare_path

    @rp_cpare_path.setter
    def rp_cpare_path(self, v: str):
        self._rp_cpare_path = v
        self._on_rp_cpare_path_changed(v)
        self.notify("rp_cpare_path")

    @property
    def file_report_result_path(self) -> str:
        return self._file_report_result_path

    @file_report_result_path.setter
    def file_report_result_path(self, v: str):
        self._file_report_result_path = v
        self.notify("file_report_result_path")

    @property
    def report_title(self) -> str:
        return self._report_title

    @report_title.setter
    def report_title(self, v: str):
        self._report_title = v

    @property
    def report_src_data(self) -> str:
        return self._report_src_data

    @report_src_data.setter
    def report_src_data(self, v: str):
        self._report_src_data = v

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

    def set_alarm_file(self, file_path: str, key: str = SC.K_EXCEL_RP_ALARM_KEY):
        if self._explorer_util.valid_sel_file(key, file_path):
            self._selected_file_dict[key] = file_path
            self.alarm_report_path = file_path
            self.file_report_result_path = SC.K_EMPTY
        else:
            self.notify("invalid_alarm_file")

    def clear_alarm_file(self, key: str = SC.K_EXCEL_RP_ALARM_KEY):
        self._selected_file_dict.pop(key, None)
        self.alarm_report_path = SC.K_EMPTY

    def set_rp_cpare_file(self, file_path: str, key: str = SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY):
        if self._explorer_util.valid_sel_file(key, file_path):
            self.rp_cpare_path = file_path
            self._dynamic_info_util.set_value("1", 2, key, SC.K_SELECT)
        else:
            self.notify("invalid_cpare_file")

    def clear_rp_cpare_file(self):
        self.rp_cpare_path = SC.K_EMPTY

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _on_rp_cpare_path_changed(self, path: str):
        if path.strip():
            self._dynamic_info_util.set_value("1", 2, SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, SC.K_SELECT)
        else:
            self._dynamic_info_util.set_value("0", 2, SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, SC.K_SELECT)

    def _on_maker_error(self, noti_key: str, noti_val: str):
        self.add_error(noti_key, noti_val)

    # ------------------------------------------------------------------ #
    # Report generation
    # ------------------------------------------------------------------ #

    def make_report(self, rp_date: str) -> bool:
        """Run report generation (called from background thread)."""
        try:
            self.clear_errors()
            if not self._selected_file_dict.get(SC.K_EXCEL_RP_ALARM_KEY):
                self.notify("no_alarm_file")
                return False

            self._dynamic_info_util.set_value(self._report_title, 2, SC.K_SCREEN_INPUT, SC.K_TITLE)
            self._dynamic_info_util.set_value(self._report_src_data, 2, SC.K_SCREEN_INPUT, SC.K_SRC_DATA)
            self._dynamic_info_util.set_value(rp_date, 2, SC.K_SCREEN_INPUT, SC.K_RP_DATE)

            if self._dynamic_info_util.update_selected_excel_info(
                    SC.K_EXCEL_RP_ALARM_KEY,
                    self._selected_file_dict[SC.K_EXCEL_RP_ALARM_KEY]) is False:
                LoggerUtil.get_logger().error(
                    f'BcCellMll make_report: required sheet not found in AL RP file: {self._selected_file_dict[SC.K_EXCEL_RP_ALARM_KEY]}'
                )
                self.notify("invalid_alarm_file")
                return False

            self._explorer_util.cp_file_to_cache_by_filekey(SC.K_EXCEL_RP_ALARM_KEY)

            cpare_selected = self._dynamic_info_util.get_value(
                2, SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, SC.K_SELECT
            )
            if cpare_selected == "1" and self._rp_cpare_path != SC.K_EMPTY:
                if self._dynamic_info_util.update_selected_excel_info(
                        SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, self._rp_cpare_path) is False:
                    self.notify("invalid_cpare_file")
                else:
                    self._explorer_util.cp_file_to_cache_by_filekey(SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY)

            #
            self._bc_cell_mll_maker.make_bc_cell_mll()

        except Exception as e:
            import traceback
            LoggerUtil.get_logger().error(
                f"BcCellMllViewModel.make_report error: {e}\n{traceback.format_exc()}")
            return False

        finally:
            self._selected_file_dict.pop(SC.K_EXCEL_RP_ALARM_KEY, None)

            self._dynamic_info_util.set_value("0", 2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_SELECT)
            self._dynamic_info_util.set_value("0", 2, SC.K_EXCEL_BC_CELL_MLL_CPARE_KEY, SC.K_SELECT)

            self.alarm_report_path = SC.K_EMPTY
            self.rp_cpare_path = SC.K_EMPTY

        LoggerUtil.get_logger().info("BcCellMllViewModel.make_report done")
        return True

    def on_make_report_finished(self, success: bool):
        """Called on main thread after background task finishes."""
        if success:
            self.file_report_result_path = (
                self._dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_OUTPUT_PATH) or ""
            )
        self.notify("make_report_finished" if success else "make_report_failed")
