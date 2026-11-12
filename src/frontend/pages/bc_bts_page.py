import flet as ft

from frontend.pages.base_page import BasePage
from frontend.viewmodels.bc_bts_vm import BcBtsViewModel
from frontend.component.background_task import run_background_task
from frontend.component.loading_overlay import LoadingOverlay
from frontend.component.rp_time_control import RpTimeControl
from frontend.component.update_db_dialog import UpdateDbDialog
from frontend.component.explorer_ui_util import ExplorerUiUtil
from frontend.component.common_view import safe_callback
from share.constant import constant as SC
from share.constant import type as ST
from share.util.dynamic_info_util import DynamicInfoUtil
from share.session import Session
from share.util.logger_util import LoggerUtil

class RpSiteControl(ft.RadioGroup):
    def __init__(self):
        initial = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1) \
            or ST.Site.ALL_SITE.value

        super().__init__(
            value=initial,
            on_change=self._on_change,
            content=ft.Row(
                controls=[
                    ft.Radio(value=ST.Site.DONG.value, label="Đông", width=150),
                    ft.Radio(value=ST.Site.TAY.value, label="Tây", width=150),
                    ft.Radio(value=ST.Site.ALL_SITE.value, label="Tất Cả Site", width=150),
                ],
                spacing=8,
            ),
        )

    def _on_change(self, e: ft.ControlEvent):
        try:
            DynamicInfoUtil().set_value(e.data, 2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        except Exception as ex:
            LoggerUtil.get_logger().error(f"RpSiteControl _on_change error: {ex}")

class DsachLoiView(ft.Column):
    def __init__(self, page: ft.Page | BasePage, parent: BasePage | None = None):
        if isinstance(page, BasePage):
            self._parent_page: BasePage | None = page
            self._page: ft.Page = page.page
        else:
            self._page: ft.Page = page
            self._parent_page: BasePage | None = parent
        self._errors: list[dict] = []

        self._list_view = ft.ListView(
            expand=False,
            height=120,
            spacing=2,
        )

        # Loading spinner shown during Excel export
        self._export_loading = ft.ProgressRing(
            width=16, height=16, stroke_width=2,
            visible=False,
        )

        self._export_btn = ft.TextButton(
            content=ft.Text(SC.K_UI_EXPORT_EXCEL),
            on_click=lambda _: self._export_to_excel(),
        )

        self._header = ft.Row(
            controls=[
                ft.Text(SC.K_UI_DSACH_LOI, weight=ft.FontWeight.W_600),
                self._export_btn,
                self._export_loading,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Bordered container wrapping the list
        _bordered_list = ft.Container(
            content=self._list_view,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=6,
            padding=4,
        )

        super().__init__(
            controls=[
                ft.Divider(),
                self._header,
                _bordered_list,
            ],
            spacing=4,
        )

    def _show_dialog(self, title: str, message: str, path: str | None = None):
        def _invoke():
            if self._parent_page is not None:
                self._parent_page.show_dialog(title=title, message=message, path=path)
            else:
                BasePage(self._page, None).show_dialog(title=title, message=message, path=path)

        try:
            async def _apply():
                try:
                    _invoke()
                except Exception as e:
                    LoggerUtil.get_logger().error(f"DsachLoiView _show_dialog error: {e}")

            self._page.run_task(_apply)
        except Exception:
            try:
                _invoke()
            except Exception as e:
                LoggerUtil.get_logger().error(f"DsachLoiView _show_dialog sync error: {e}")

    def _safe_update(self):
        try:
            async def _do_update():
                try:
                    self.update()
                except Exception:
                    pass
                try:
                    self._page.update()
                except Exception:
                    pass

            self._page.run_task(_do_update)
        except Exception as e:
            LoggerUtil.get_logger().error(f"DsachLoiView _safe_update error: {e}")

    def add_error(self, error_key: str, error_des: str):
        """Append one error row and refresh the UI."""
        item = {SC.K_UI_ERROR: error_key, SC.K_UI_DESCRIPTION: error_des}
        if item in self._errors:
            return

        self._errors.append(item)

        self._list_view.controls.append(
            ft.Container(
                content=ft.Text(
                    f"{error_key} : {error_des}",
                    selectable=True,
                    color=ft.Colors.ERROR,
                ),
                padding=ft.Padding.symmetric(horizontal=4, vertical=2),
            )
        )

        self._safe_update()

    def clear_errors(self):
        """Clear all errors and reset the list."""
        self._errors.clear()
        self._list_view.controls.clear()
        self._safe_update()

    @property
    def error_list(self) -> list[dict]:
        return self._errors

    def has_errors(self) -> bool:
        return len(self._errors) > 0

    def _set_loading(self, loading: bool):
        self._export_btn.disabled = loading
        self._export_loading.visible = loading
        self._safe_update()

    def _export_to_excel(self):
        if not self._errors:
            self._show_dialog(title="Thông báo", message="Không có lỗi để xuất")
            return

        def _do_export():
            self._set_loading(True)
            try:
                ret_excel_path = BcBtsViewModel().write_excel_dsach_loi(data=self._errors)
                self._show_dialog(
                    title="Thông báo",
                    message=f"Đã xuất Excel: {ret_excel_path}",
                    path=ret_excel_path,
                )
            except Exception as e:
                LoggerUtil.get_logger().error(f"DsachLoiView _export_to_excel error: {e}")
                self._show_dialog(title="Thông báo", message=f"Lỗi xuất Excel")
            finally:
                self._set_loading(False)

        self._page.run_thread(_do_export)

class BcBtsPage(BasePage):
    title = ST.ReportTypeInfo.BC_BTS.report_name
    RpSiteControl = RpSiteControl
    DsachLoiView = DsachLoiView

    def __init__(self, page: ft.Page, router, **kwargs):
        super().__init__(page, router)
        self._vm = BcBtsViewModel()
        self._vm.subscribe("is_loading", self._on_loading)
        self._vm.subscribe("alarm_report_path", self._on_alarm_path)
        self._vm.subscribe("rp_nclr_cpare_path", self._on_cpare_path)
        self._vm.subscribe("report_src_data", self._on_src_data)
        self._vm.subscribe("errors", self._on_errors)
        self._vm.subscribe("no_alarm_file", lambda: self.show_dialog("Thông báo", "Chưa chọn file Alarm Report"))
        self._vm.subscribe("invalid_alarm_file", lambda: self.show_dialog("Thông báo", SC.K_UI_INVALID))
        self._vm.subscribe("make_report_finished", lambda: self._on_finished(True))
        self._vm.subscribe("make_report_failed", lambda: self._on_finished(False))

        self._explorer_util = ExplorerUiUtil()
        self._explorer_util.register(page)
        self._update_db_dialog: UpdateDbDialog | None = None

    # ------------------------------------------------------------------ #
    # Build
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        dynamic_info = DynamicInfoUtil()

        # --- Report type radio ---
        initial_rp_type = self._vm.sel_rp_type
        self._rp_type_group = ft.RadioGroup(
            value=initial_rp_type,
            on_change=self._on_rp_type_changed,
            content=ft.Row([
                ft.Radio(
                    value=ST.ReportTypeInfo.BC_CBAO_MLL.report_id.name,
                    label=ST.ReportTypeInfo.BC_CBAO_MLL.report_name,
                    width=150,
                ),
                ft.Radio(
                    value=ST.ReportTypeInfo.BC_MPD.report_id.name,
                    label=ST.ReportTypeInfo.BC_MPD.report_name,
                    width=150,
                ),
                ft.Radio(
                    value=ST.ReportTypeInfo.TGHOP_BTS.report_id.name,
                    label=ST.ReportTypeInfo.TGHOP_BTS.report_name,
                    width=150,
                ),
            ], spacing=8),
        )

        # --- Site ---
        self._site_ctrl = RpSiteControl()

        # --- Report time (from-to) ---
        self._rp_time_ctrl = RpTimeControl(self.page, mode="from_to")

        # --- Report data source ---
        self._src_data_field = ft.TextField(
            label=SC.K_UI_REPORT_DATA_SRC,
            value=self._vm.report_src_data,
            dense=True,
            on_blur=lambda e: setattr(self._vm, "report_src_data", e.control.value),
            expand=True,
        )

        # --- RP time compare (BC MLL CLR) — inlined ---
        self._rp_time_compare_field = ft.TextField(
            label="G.Trị",
            value=dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE_BC_MLL) or "",
            dense=True, width=70,
            on_blur=lambda e: (
                setattr(e.control, 'value', str(int(e.control.value))) \
                    if e.control.value.strip().isdigit() else None,
                dynamic_info.set_value(
                    e.control.value, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_COMPARE_BC_MLL
                ),
                e.control.update() if e.control.value.strip().isdigit() else None,
            )[-1],
        )
        self._rp_year_compare_field = ft.TextField(
            label="Năm",
            value=dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_YEAR_COMPARE) or "",
            dense=True, width=70,
            on_blur=lambda e: dynamic_info.set_value(e.control.value, 2, SC.K_SCREEN_INPUT, SC.K_RP_YEAR_COMPARE),
        )
        self._rp_time_cpare_number_field = ft.TextField(
            label="S.Lượng",
            value=self._vm.rp_time_cpare_number,
            dense=True, width=90,
            on_blur=lambda e: (
                setattr(e.control, 'value', str(int(e.control.value))) \
                    if e.control.value.strip().isdigit() else None,
                setattr(self._vm, "rp_time_cpare_number", e.control.value),
                e.control.update() if e.control.value.strip().isdigit() else None,
            )[-1],
        )

        # --- Time type (Tuần/Tháng + value) — inlined ---
        self._rp_time_type_dropdown = ft.Dropdown(
            label="Loại TGian",
            width=120,
            dense=True,
            options=[
                ft.dropdown.Option(ST.TimeType.WEEK.value),
                ft.dropdown.Option(ST.TimeType.MONTH.value),
            ],
            value=dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE) \
                or ST.TimeType.WEEK.value,
            on_select=lambda e: dynamic_info.set_value(
                e.control.value, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE),
        )
        self._rp_time_value_field = ft.TextField(
            label="G.Trị",
            value=dynamic_info.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME) or "",
            dense=True, width=70,
            on_blur=lambda e: dynamic_info.set_value(e.control.value, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME),
        )

        # --- Compare NCLR file ---
        self._cpare_field = ft.TextField(
            label="So Sánh BC NCLR",
            read_only=True, dense=True, expand=True,
        )

        # --- Alarm file ---
        self._alarm_field = ft.TextField(
            label="Alarm Report",
            read_only=True, dense=True, expand=True,
        )

        # --- Error list ---
        self._dsach_loi = DsachLoiView(self.page, parent=self)

        # --- Make report ---
        self._make_btn = ft.Button(
            content=ft.Text("Tạo Báo Cáo", size=18),
            icon=ft.Icons.PLAY_ARROW,
            on_click=lambda _: self._start_make_report(),
        )

        # --- Loading overlay ---
        self._overlay = LoadingOverlay(message="Đang Tải...")

        # ---- Config section ----
        config_section = self._build_config_section()

        main_content = ft.Container(
            content=ft.Column(
                controls=[
                    self._form_row("Loại Báo Cáo", self._rp_type_group),
                    self._form_row(SC.K_SITE, self._site_ctrl),
                    self._form_row(
                        SC.K_UI_REPORT_DATA_SRC, self._src_data_field),
                    self._form_row(SC.K_UI_REPORT_TIME,
                                   ft.Row([self._rp_time_type_dropdown,
                                           self._rp_time_value_field,
                                           self._rp_time_ctrl], spacing=8)),
                    self._form_row(
                        "So Sánh BC MLL CLR",
                        ft.Row([
                            ft.Container(width=120),
                            self._rp_time_compare_field,
                            self._rp_year_compare_field,
                            ft.Text("Biểu đồ:"),
                            self._rp_time_cpare_number_field], spacing=8)
                    ),
                    self._form_row(
                        "So Sánh BC MLL NCLR",
                        ft.Row([
                            ft.IconButton(ft.Icons.FOLDER_OPEN, on_click=lambda _: self._pick_cpare_file(),
                                          tooltip=SC.K_UI_SEL),
                            ft.IconButton(ft.Icons.CLEAR, on_click=lambda _: self._vm.clear_rp_cpare_file(),
                                          tooltip=SC.K_UI_CLEAR),
                            self._cpare_field,
                        ], spacing=4)
                    ),
                    ft.Divider(),
                    self._form_row(
                        "Alarm Report",
                        ft.Row([
                            ft.IconButton(ft.Icons.FOLDER_OPEN, on_click=lambda _: self._pick_alarm_file(),
                                          tooltip=SC.K_UI_SEL),
                            ft.IconButton(ft.Icons.CLEAR, on_click=lambda _: self._vm.clear_alarm_file(),
                                          tooltip=SC.K_UI_CLEAR),
                            self._alarm_field,
                        ], spacing=4)
                    ),
                    ft.Row([self._make_btn], alignment=ft.MainAxisAlignment.CENTER),
                    self._dsach_loi,
                    ft.Divider(),
                    config_section,
                    ft.Container(height=16),
                ],
                spacing=16,
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
        config_control_height = 60
        config_control_width = 200
        config_border_radius = 6
        config_content_padding = ft.Padding(left=12, top=0, right=12, bottom=0)

        def config_tile(
            content: ft.Control,
            padding: ft.Padding | None = None,
        ) -> ft.Container:
            return ft.Container(
                content=content,
                height=config_control_height,
                width=config_control_width,
                padding=padding,
                border=ft.Border.all(1, ft.Colors.OUTLINE),
                border_radius=config_border_radius,
                alignment=ft.Alignment.CENTER,
            )

        # Th.gian c.báo
        self._tgian_cb_field = ft.TextField(
            label="Th.Gian C.Báo",
            value=self._vm.tgian_cb,
            dense=True,
            border=ft.InputBorder.NONE,
            content_padding=config_content_padding,
            on_blur=lambda e: setattr(self._vm, "tgian_cb", e.control.value),
        )

        # Loại đ.mối q.lý
        self._loai_dmoi_dropdown = ft.Dropdown(
            label="Đ.Mối Q.Lý",
            dense=True,
            border=ft.InputBorder.NONE,
            content_padding=ft.Padding(left=12, top=8, right=12, bottom=0),
            options=[ft.dropdown.Option("0"), ft.dropdown.Option("1")],
            value=self._vm.loai_dmoi_qly,
            on_select=lambda e: setattr(self._vm, "loai_dmoi_qly", e.control.value),
        )

        controls = [
            config_tile(self._tgian_cb_field),
            config_tile(self._loai_dmoi_dropdown),
        ]

        # Admin-only
        if Session.get_role() == "admin":
            self._save_db_check = ft.Checkbox(
                label="Lưu DB BC MLL CLR",
                value=self._vm.save_ret_bc_mll_to_db,
                on_change=lambda e: setattr(self._vm, "save_ret_bc_mll_to_db", e.control.value),
            )
            save_db_box = config_tile(
                content=self._save_db_check,
                padding=ft.Padding(left=10, top=0, right=12, bottom=0),
            )
            update_db_btn = ft.OutlinedButton(
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
            controls.extend([save_db_box, update_db_btn])

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
                LoggerUtil.get_logger().error(f"BcBtsPage _on_loading error: {e}")

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
            self._cpare_field.value = self._vm.rp_nclr_cpare_path
            self._cpare_field.update()
        except Exception:
            pass

    def _on_src_data(self):
        try:
            self._src_data_field.value = self._vm.report_src_data
            self._src_data_field.update()
        except Exception:
            pass

    def _on_errors(self):
        errors = self._vm.errors
        if errors:
            last = errors[-1]
            self._dsach_loi.add_error(last[SC.K_UI_ERROR], last[SC.K_UI_DESCRIPTION])

    @safe_callback(lambda self: self.page)
    def _on_finished(self, success: bool):
        if success:
            msg = \
                "Hoàn thành với lỗi" if self._dsach_loi.has_errors() else "Hoàn Thành"
            path = self._vm.file_report_result_path
            self.show_dialog(
                title="Thông báo",
                message=f'{msg} :  {path}',
                path=path
            )
        else:
            self.show_dialog(title="Thông báo", message= "Lỗi")

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _on_rp_type_changed(self, e: ft.ControlEvent):
        self._vm.sel_rp_type = e.control.value

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
        run_background_task(
            page=self.page,
            vm=self._vm,
            task_fn=self._vm.make_report,
            finish_fn=self._vm.on_make_report_finished,
        )

    @safe_callback(lambda self: self.page)
    def _open_update_db(self):
        self._update_db_dialog = UpdateDbDialog(
            self.page,
            self._vm.get_db_update_list(),
        )
        self._update_db_dialog.open()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _form_row(label: str, control: ft.Control) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(label, weight=ft.FontWeight.W_600),
                    width=140,
                ),
                ft.Container(content=control, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

    @staticmethod
    def _section(title: str, control: ft.Control) -> ft.Column:
        return ft.Column(
            controls=[
                ft.Text(title, weight=ft.FontWeight.W_600,
                        color=ft.Colors.SECONDARY),
                control,
            ],
            spacing=4,
        )

    def add_error(self, error_key: str, error_des: str):
        """Append error to DsachLoiView."""
        self._dsach_loi.add_error(error_key, error_des)

    def clear_errors(self):
        """Clear error list in DsachLoiView."""
        self._dsach_loi.clear_errors()

    def has_errors(self) -> bool:
        """Check if DsachLoiView has errors."""
        return self._dsach_loi.has_errors()

