import flet as ft

from frontend.pages.base_page import BasePage
from frontend.viewmodels.db_config_vm import DbConfigViewModel
from frontend.component.db_config_dialog import DbConfigDialog
from share.constant import constant as SC


class DbConfigPage(BasePage):
    title = "Kiểm Tra Kết Nối CSDL"
    show_back_button = False
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    scroll = None

    def __init__(self, page: ft.Page, router, **kwargs):
        super().__init__(page, router)
        self._vm = DbConfigViewModel()
        self._dialog: DbConfigDialog | None = None

        # Subscribe to VM changes
        self._vm.subscribe("status_message", self._on_status_changed)
        self._vm.subscribe("is_loading", self._on_loading_changed)
        self._vm.subscribe("is_connected", self._on_connected_changed)

    # ------------------------------------------------------------------ #
    # Build UI
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        self._status_text = ft.Text(
            self._vm.status_message,
            size=14,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.W_500,
        )
        self._spinner = ft.ProgressRing(
            width=36, height=36, stroke_width=3,
            color=ft.Colors.PRIMARY,
            visible=True,
        )
        self._retry_btn = ft.ElevatedButton(
            content=ft.Text("Thử Lại", size=14, weight=ft.FontWeight.W_600),
            icon=ft.Icons.REFRESH,
            on_click=lambda _: self._check_connection(),
            visible=False,
            width=320,
            height=44,
            bgcolor=ft.Colors.PRIMARY,
            color=ft.Colors.ON_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        self._config_btn = ft.OutlinedButton(
            content=ft.Text("Cấu Hình DB", size=14, weight=ft.FontWeight.W_500),
            icon=ft.Icons.SETTINGS,
            on_click=lambda _: self._open_config(),
            visible=False,
            width=320,
            height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        # Logo / Storage Icon Badge
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.STORAGE_ROUNDED,
                                size=36,
                                color=ft.Colors.PRIMARY,
                            ),
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            width=64,
                            height=64,
                            border_radius=32,
                            alignment=ft.Alignment.CENTER,
                        ),
                        # App Title & Subtitle
                        ft.Text(
                            "OMC Management Tool",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PRIMARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Kiểm tra kết nối CSDL",
                            size=13,
                            color=ft.Colors.OUTLINE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=4),
                        ft.Divider(color=ft.Colors.OUTLINE_VARIANT, height=1),
                        ft.Container(height=8),
                        # Status indicator
                        self._spinner,
                        self._status_text,
                        ft.Container(height=8),
                        # Buttons
                        self._retry_btn,
                        self._config_btn,
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    width=340,
                ),
                padding=ft.Padding.symmetric(vertical=32, horizontal=28),
            ),
            elevation=4,
        )

        # Start check immediately after build
        self.page.run_thread(self._check_connection_thread)

        return ft.Container(
            content=card,
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=20,
        )

    # ------------------------------------------------------------------ #
    # VM subscribers
    # ------------------------------------------------------------------ #

    def _on_status_changed(self):
        try:
            self._status_text.value = self._vm.status_message
            self._status_text.update()
        except Exception:
            pass

    def _on_loading_changed(self):
        try:
            self._spinner.visible = self._vm.is_loading
            self._spinner.update()
        except Exception:
            pass

    def _on_connected_changed(self):
        connected = self._vm.is_connected
        try:
            self._retry_btn.visible = not connected
            self._config_btn.visible = not connected
            self._retry_btn.update()
            self._config_btn.update()
        except Exception:
            pass
        if connected:
            # Navigate to Login after a short delay
            async def _delayed_nav():
                import asyncio
                await asyncio.sleep(0.6)
                self.router.replace("login")
            self.page.run_task(_delayed_nav)

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _check_connection_thread(self):
        self._vm.check_connection()

    def _check_connection(self):
        self.page.run_thread(self._check_connection_thread)

    def _open_config(self):
        if self._dialog is None:
            self._dialog = DbConfigDialog(
                self.page,
                on_saved=lambda: self._check_connection(),
            )
        self._dialog.open()
