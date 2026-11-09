import flet as ft

from frontend.pages.base_page import BasePage
from frontend.viewmodels.login_vm import LoginViewModel
from frontend.component.db_config_dialog import DbConfigDialog
from share.constant import constant as SC


class LoginPage(BasePage):
    title = "Đăng Nhập"
    show_back_button = False

    def __init__(self, page: ft.Page, router, **kwargs):
        super().__init__(page, router)
        self._vm = LoginViewModel(
            on_login_success=lambda role: self.router.replace("home")
        )
        self._vm.subscribe("error_message", self._on_error_changed)
        self._vm.subscribe("is_loading", self._on_loading_changed)
        self._config_dialog: DbConfigDialog | None = None

    # ------------------------------------------------------------------ #
    # Build UI
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        self._username_field = ft.TextField(
            label="Tài khoản",
            hint_text="Nhập tên đăng nhập",
            prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            autofocus=True,
            on_change=lambda e: setattr(self._vm, "username", e.control.value),
            on_submit=lambda _: self._do_login(),
            border_radius=10,
            dense=True,
        )
        self._password_field = ft.TextField(
            label="Mật khẩu",
            hint_text="Nhập mật khẩu",
            prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
            password=True,
            can_reveal_password=True,
            on_change=lambda e: setattr(self._vm, "password", e.control.value),
            on_submit=lambda _: self._do_login(),
            border_radius=10,
            dense=True,
        )
        self._error_text = ft.Text(
            "",
            color=ft.Colors.ERROR,
            size=12,
            visible=False,
            text_align=ft.TextAlign.CENTER,
        )
        self._spinner = ft.ProgressRing(
            width=18,
            height=18,
            stroke_width=2.5,
            visible=False,
        )
        self._login_btn = ft.ElevatedButton(
            content=ft.Text("Đăng Nhập", size=14, weight=ft.FontWeight.W_600),
            icon=ft.Icons.LOGIN_ROUNDED,
            on_click=lambda _: self._do_login(),
            width=320,
            height=44,
            bgcolor=ft.Colors.PRIMARY,
            color=ft.Colors.ON_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        self._admin_dev_btn = ft.OutlinedButton(
            content=ft.Text("Đăng Nhập Admin-Dev", size=14, weight=ft.FontWeight.W_500),
            icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            on_click=lambda _: self._vm.admin_login(),
            width=320,
            height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        self._guest_btn = ft.OutlinedButton(
            content=ft.Text("Đăng Nhập Khách", size=14, weight=ft.FontWeight.W_500),
            icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
            on_click=lambda _: self._vm.guest_login(),
            width=320,
            height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        self._config_btn = ft.TextButton(
            content=ft.Text("Cấu Hình CSDL", size=13, weight=ft.FontWeight.W_500),
            icon=ft.Icons.SETTINGS_OUTLINED,
            on_click=lambda _: self._open_db_config(),
            width=320,
            height=40,
        )

        card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        # Logo / Icon Badge
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.ANALYTICS_ROUNDED,
                                size=36,
                                color=ft.Colors.PRIMARY,
                            ),
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            width=64,
                            height=64,
                            border_radius=32,
                            alignment=ft.Alignment.CENTER,
                        ),
                        # App Title & Description
                        ft.Text(
                            "OMC Report Tool",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PRIMARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=4),
                        ft.Divider(color=ft.Colors.OUTLINE_VARIANT, height=1),
                        ft.Container(height=4),
                        # Input Fields
                        self._username_field,
                        self._password_field,
                        # Error / Status Area
                        ft.Row(
                            [self._spinner, self._error_text],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        ft.Container(height=4),
                        # Action Buttons (Vertical Stack)
                        self._login_btn,
                        self._guest_btn,
                        self._admin_dev_btn, ############################################## DEV ONLY
                        self._config_btn,
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    width=320,
                ),
                padding=ft.Padding.symmetric(vertical=32, horizontal=28),
            ),
            elevation=4,
        )

        return ft.Container(
            content=ft.Column(
                controls=[card],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=20,
        )

    # ------------------------------------------------------------------ #
    # VM subscribers
    # ------------------------------------------------------------------ #

    def _on_error_changed(self):
        msg = self._vm.error_message
        try:
            self._error_text.value = msg
            self._error_text.visible = bool(msg)
            self._error_text.update()
        except Exception:
            pass

    def _on_loading_changed(self):
        loading = self._vm.is_loading
        try:
            self._spinner.visible = loading
            self._login_btn.disabled = loading
            self._guest_btn.disabled = loading
            self._spinner.update()
            self._login_btn.update()
            self._guest_btn.update()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _do_login(self):
        self._vm.login()

    def _open_db_config(self):
        if self._config_dialog is None:
            self._config_dialog = DbConfigDialog(self.page)
        self._config_dialog.open()
