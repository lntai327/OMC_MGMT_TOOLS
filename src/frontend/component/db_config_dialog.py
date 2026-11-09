from typing import Callable, Optional

import flet as ft

from backend.db.sqlserver import SqlServer
from backend.repositories.account.account import AccountService
from frontend.viewmodels.db_config_vm import DbConfigViewModel

from share.constant import constant as SC
from share.util.logger_util import LoggerUtil

class DbConfigDialog:
    """Modal dialog for viewing and editing DB connection credentials.

    Usage:
        dlg = DbConfigDialog(page, account_service, on_saved=lambda: vm.check_connection())
        dlg.open()
    """

    def __init__(
        self,
        page: ft.Page,
        account_service: Optional[AccountService] = None,
        on_saved: Optional[Callable] = None,
    ):
        self._page = page
        self._account_service = account_service or AccountService()
        self._on_saved = on_saved
        self._vm = DbConfigViewModel()

        self._show_password = False

        # Fields
        self._server_field = ft.TextField(
            label="Server", read_only=True, dense=True,
            color=ft.Colors.SECONDARY,
        )
        self._db_field = ft.TextField(
            label="Database", read_only=True, dense=True,
            color=ft.Colors.SECONDARY,
        )
        self._username_field = ft.TextField(
            label="Tài khoản", dense=True, autofocus=True,
        )
        self._password_field = ft.TextField(
            label="Mật khẩu", dense=True,
            password=True,
            can_reveal_password=True,
        )
        self._status_text = ft.Text("", color=ft.Colors.ERROR, size=12)

        self._dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Tài Khoản DB", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    self._server_field,
                    self._db_field,
                    ft.Divider(),
                    self._username_field,
                    self._password_field,
                    self._status_text,
                    ft.Container(height=4),
                    ft.ElevatedButton(
                        content=ft.Text(SC.K_UI_SAVE, size=14, weight=ft.FontWeight.W_600),
                        width=340,
                        height=44,
                        bgcolor=ft.Colors.PRIMARY,
                        color=ft.Colors.ON_PRIMARY,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        on_click=self._save,
                    ),
                    ft.OutlinedButton(
                        content=ft.Text("Đóng", size=14, weight=ft.FontWeight.W_500),
                        width=340,
                        height=44,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        on_click=lambda _: self.close(),
                    ),
                ],
                tight=True,
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=340,
            ),
        )

        page.overlay.append(self._dialog)
        self._load_config()

    # ------------------------------------------------------------------ #

    def open(self):
        self._load_config()
        self._status_text.value = ""
        self._dialog.open = True
        self._page.update()

    def close(self):
        self._dialog.open = False
        self._page.update()

    # ------------------------------------------------------------------ #

    def _load_config(self):
        cfg = SqlServer().get_db_config()
        self._server_field.value = cfg.get(SC.K_SERVER, "")
        self._db_field.value = cfg.get(SC.K_DB, "")
        self._username_field.value = cfg.get(SC.K_USERNAME, "")
        self._password_field.value = ""

    def _save(self, _):
        username = (self._username_field.value or "").strip()
        password = self._password_field.value or ""

        if not username:
            self._status_text.value = "Nhập tài khoản"
            self._status_text.color = ft.Colors.ERROR
            self._page.update()
            return

        if not password:
            self._status_text.value = "Nhập mật khẩu"
            self._status_text.color = ft.Colors.ERROR
            self._page.update()
            return

        self._status_text.value = "Đang kiểm tra kết nối CSDL..."
        self._status_text.color = ft.Colors.PRIMARY
        self._page.update()

        conn_ok = self._vm.check_connection(username, password)
        if not conn_ok:
            self._status_text.value = "Kết nối thất bại. Kiểm tra lại tài khoản/mật khẩu"
            self._status_text.color = ft.Colors.ERROR
            self._page.update()
            return

        ok = self._account_service.save_db_account(username, password)
        if ok:
            self._status_text.value = "Lưu thành công"
            self._status_text.color = ft.Colors.GREEN
            self._page.update()
            if callable(self._on_saved):
                self._on_saved()
        else:
            self._status_text.value = "Lưu thất bại"
            self._status_text.color = ft.Colors.ERROR
            self._page.update()
