import flet as ft

from frontend.pages.base_page import BasePage
from frontend.viewmodels.bc_cell_mll_vm import BcCellMllViewModel
from frontend.component.background_task import run_background_task
from frontend.component.loading_overlay import LoadingOverlay
from frontend.component.dsach_loi_view import DsachLoiView
from frontend.component.rp_site_control import RpSiteControl
from frontend.component.rp_time_control import RpTimeControl
from frontend.component.update_db_dialog import UpdateDbDialog
from frontend.component.explorer_ui_util import ExplorerUiUtil
import frontend.constant.type as FET
from frontend.component.common_view import safe_callback
from share.session import Session
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil

class BcCellMllPage(BasePage):
    title = FET.ReportTypeInfo.BC_CELL_MLL.report_name

    def __init__(self, page: ft.Page, router, **kwargs):
        super().__init__(page, router)
        self._vm = BcCellMllViewModel()
        self._vm.subscribe("is_loading", self._on_loading)
        self._vm.subscribe("alarm_report_path", self._on_alarm_path)
        self._vm.subscribe("rp_cpare_path", self._on_cpare_path)
        self._vm.subscribe("file_report_result_path", self._on_result_path)
        self._vm.subscribe("errors", self._on_errors)
        self._vm.subscribe("no_alarm_file", lambda: self.show_dialog("Lỗi", "Chưa chọn file Alarm Report"))
        self._vm.subscribe("invalid_alarm_file", lambda: self.show_dialog("Lỗi", "File không hợp lệ"))
        self._vm.subscribe("make_report_finished", lambda: self.show_dialog("Thông báo", "Hoàn Thành"))
        self._vm.subscribe("make_report_failed", lambda: self.show_dialog("Lỗi", "Tạo BC thất bại"))

        self._explorer_util = ExplorerUiUtil()
        self._explorer_util.register(page)
        self._update_db_dialog: UpdateDbDialog | None = None
        self._update_db_btn: ft.OutlinedButton | None = None

    # ------------------------------------------------------------------ #
    # Build
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        # --- Site control ---
        self._site_control = RpSiteControl()

        # --- Report title ---
        self._title_field = ft.TextField(
            label=SC.K_UI_REPORT_TITLE,
            value=self._vm.report_title,
            dense=True,
            on_blur=lambda e: setattr(self._vm, "report_title", e.control.value),
            expand=True,
        )

        # --- Report data source ---
        self._src_data_field = ft.TextField(
            label=SC.K_UI_REPORT_DATA_SRC,
            value=self._vm.report_src_data,
            dense=True,
            on_blur=lambda e: setattr(self._vm, "report_src_data", e.control.value),
            expand=True,
        )

        # --- Report time (single date) ---
        self._rp_time_ctrl = RpTimeControl(self.page, mode="single")

        # --- Compare BC ---
        self._cpare_field = ft.TextField(
            label="So Sánh BC",
            value="",
            read_only=True,
            dense=True,
            expand=True,
            hint_text="(tuỳ chọn)",
        )
        cpare_pick_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip=SC.K_UI_SEL,
            on_click=lambda _: self._pick_cpare_file(),
        )
        cpare_clear_btn = ft.IconButton(
            icon=ft.Icons.CLEAR,
            tooltip=SC.K_UI_CLEAR,
            on_click=lambda _: self._vm.clear_rp_cpare_file(),
        )

        # --- Alarm report ---
        self._alarm_field = ft.TextField(
            label="Alarm Report",
            value="",
            read_only=True,
            dense=True,
            expand=True,
        )
        alarm_pick_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip=SC.K_UI_SEL,
            on_click=lambda _: self._pick_alarm_file(),
        )
        alarm_clear_btn = ft.IconButton(
            icon=ft.Icons.CLEAR,
            tooltip=SC.K_UI_CLEAR,
            on_click=lambda _: self._vm.clear_alarm_file(),
        )

        # --- Result ---
        self._result_field = ft.TextField(
            label=SC.K_UI_REPORT_RESULT,
            value="",
            read_only=True,
            dense=True,
            expand=True,
        )
        result_open_btn = ft.IconButton(
            icon=ft.Icons.OPEN_IN_NEW,
            tooltip=SC.K_UI_OPEN,
            on_click=lambda _: self._explorer_util.show_in_explorer(self._vm.file_report_result_path),
        )

        # --- Error list ---
        self._dsach_loi = DsachLoiView(self.page)

        # --- Make report button ---
        self._make_btn = ft.Button(
            content=ft.Text(SC.K_UI_MAKE_REPORT),
            icon=ft.Icons.PLAY_ARROW,
            on_click=lambda _: self._start_make_report(),
        )

        # --- Loading overlay ---
        self._overlay = LoadingOverlay()

        # ---- Config section ----
        config_section = self._build_config_section()

        main_content = ft.Container(
            content=ft.Column(
                controls=[
                    self._form_row(SC.K_SITE, self._site_control),
                    self._form_row(SC.K_UI_REPORT_TITLE, self._title_field),
                    self._form_row(SC.K_UI_REPORT_DATA_SRC, self._src_data_field),
                    self._form_row(SC.K_UI_REPORT_TIME, self._rp_time_ctrl),
                    self._form_row(
                        SC.K_UI_RP_COMPARE,
                        ft.Row(
                            [cpare_pick_btn, cpare_clear_btn,
                            self._cpare_field], spacing=4
                        )
                    ),
                    ft.Divider(),
                    self._form_row(
                        "Alarm Report",
                        ft.Row(
                            [alarm_pick_btn, alarm_clear_btn,
                            self._alarm_field], spacing=4)
                        ),
                    self._form_row(
                        SC.K_UI_REPORT_RESULT,
                        ft.Row(
                            [result_open_btn, ft.Container(width=40),
                            self._result_field],
                            spacing=4
                        )
                    ),
                    ft.Row(
                        [self._make_btn],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    self._dsach_loi,
                    *( [ft.Divider()] if Session.get_role() == "admin" else [] ),
                    config_section,
                    ft.Container(height=16),
                ],
                spacing=10,
            ),
            padding=ft.Padding.all(20),
        )

        scroll_col = ft.Column(
            controls=[main_content],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self._interactive_root = scroll_col

        return ft.Stack(
            controls=[
                scroll_col,
                self._overlay,
            ],
            expand=True,
        )

    # ------------------------------------------------------------------ #
    # Config section
    # ------------------------------------------------------------------ #

    def _build_config_section(self) -> ft.Control:
        config_control_height = 100
        config_control_width = 200
        config_border_radius = 6

        controls = []

        # Admin-only
        if Session.get_role() == "admin":
            self._update_db_btn = ft.OutlinedButton(
                content=ft.Text(SC.K_UI_UPDATE_DB),
                icon=ft.Icons.UPLOAD_FILE,
                height=config_control_height,
                width=config_control_width,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=config_border_radius),
                    padding=ft.Padding(left=18, top=0, right=18, bottom=0),
                ),
                on_click=lambda _: self._open_update_db(),
            )
            controls.append(
                self._update_db_btn
            )

        return ft.Row(
            controls=controls,
            spacing=16,
            run_spacing=12,
            wrap=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # ------------------------------------------------------------------ #
    # VM subscribers
    # ------------------------------------------------------------------ #

    def _on_loading(self):
        loading = self._vm.is_loading

        async def _apply():
            try:
                if loading:
                    self._overlay.show()
                else:
                    self._overlay.hide()
                self.set_controls_disabled(self._interactive_root, loading)
                self.page.update()
            except Exception as e:
                LoggerUtil.get_logger().error(f"BcCellMllPage _on_loading error: {e}")

        try:
            self.page.run_task(_apply)
        except Exception:
            pass

    def _on_alarm_path(self):
        try:
            self._alarm_field.value = self._vm.alarm_report_path
            self._alarm_field.update()
        except Exception:
            pass

    def _on_cpare_path(self):
        try:
            self._cpare_field.value = self._vm.rp_cpare_path
            self._cpare_field.update()
        except Exception:
            pass

    def _on_result_path(self):
        try:
            self._result_field.value = self._vm.file_report_result_path
            self._result_field.update()
        except Exception:
            pass

    def _on_errors(self):
        errors = self._vm.errors
        if errors:
            last = errors[-1]
            self._dsach_loi.add_error(last[SC.K_UI_ERROR], last[SC.K_UI_DESCRIPTION])

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    @safe_callback(lambda self: self.page)
    def _pick_alarm_file(self):
        self._explorer_util.pick_file(
            on_result=lambda p: self._vm.set_alarm_file(p) if p else None,
            allowed_extensions=["xlsx", "xls"],
        )

    @safe_callback(lambda self: self.page)
    def _pick_cpare_file(self):
        self._explorer_util.pick_file(
            on_result=lambda p: self._vm.set_rp_cpare_file(p) if p else None,
            allowed_extensions=["xlsx", "xls"],
        )

    @safe_callback(lambda self: self.page)
    def _start_make_report(self):
        self._dsach_loi.clear_errors()
        self._vm.clear_errors()
        rp_date = self._rp_time_ctrl.date_single
        run_background_task(
            page=self.page,
            vm=self._vm,
            task_fn=lambda: self._vm.make_report(rp_date),
            finish_fn=self._vm.on_make_report_finished,
        )

    @safe_callback(lambda self: self.page)
    def _open_update_db(self):
        if self._update_db_dialog is None:
            self._update_db_dialog = UpdateDbDialog(
                self.page,
                self._vm.DB_NEED_UPDATE_LIST,
            )
        self._update_db_dialog.open()

    # ------------------------------------------------------------------ #
    # Helper
    # ------------------------------------------------------------------ #

    @staticmethod
    def _form_row(label: str, control: ft.Control) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(label, weight=ft.FontWeight.W_600),
                    width=110,
                ),
                ft.Container(content=control, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )