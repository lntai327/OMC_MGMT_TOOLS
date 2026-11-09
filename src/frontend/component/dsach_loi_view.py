from __future__ import annotations
import threading

import flet as ft

from share.util.logger_util import LoggerUtil
from backend.repositories.common.dsach_loi.dsach_loi_writer import ExcelDsachLoiWriter
from share.constant import constant as SC


class DsachLoiView(ft.Column):
    """Error list panel with Clear and Export-to-Excel actions.

    Usage:
        view = DsachLoiView(page)
        view.add_error("key", "description")
        view.clear_errors()
    """

    def __init__(self, page: ft.Page):
        self._page = page
        self._errors: list[dict] = []

        self._list_view = ft.ListView(
            expand=False,
            height=120,
            spacing=2,
        )
        self._noti_text = ft.Text(
            "", italic=True,
            color=ft.Colors.SECONDARY,
            visible=False,
            size=12,
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
                ft.Text(SC.K_UI_DSACH_LOI, weight=ft.FontWeight.W_600, size=13),
                ft.TextButton(
                    content=ft.Text(SC.K_UI_CLEAR),
                    on_click=lambda _: self.clear_errors(),
                ),
                ft.TextButton(
                    content=ft.Text("Sao chép"),
                    on_click=lambda _: self.copy_all_errors(),
                ),
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
                self._noti_text,
                _bordered_list,
            ],
            spacing=4,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _safe_update(self): #Need review
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
            LoggerUtil.get_logger().error(f"DsachLoiView._safe_update error: {e}")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

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
                    size=12,
                    selectable=True,
                    color=ft.Colors.ERROR,
                ),
                padding=ft.Padding.symmetric(horizontal=4, vertical=2),
            )
        )
        # Hide noti while errors are present
        self._noti_text.visible = False
        self._safe_update()

    def clear_errors(self):
        """Clear all errors and reset the list."""
        self._errors.clear()
        self._list_view.controls.clear()
        self._noti_text.value = ""
        self._noti_text.visible = False
        self._safe_update()

    def copy_all_errors(self):
        """Copy all error text lines to the system clipboard."""
        if not self._errors:
            self._set_noti("Không có dữ liệu để sao chép")
            return

        all_text = "\n".join(
            f"{item[SC.K_UI_ERROR]} : {item[SC.K_UI_DESCRIPTION]}"
            for item in self._errors
        )
        async def _do_copy():
            try:
                await self._page.clipboard.set(all_text)
                self._set_noti("✓ Đã sao chép tất cả lỗi vào Clipboard")
            except Exception as e:
                LoggerUtil.get_logger().error(f"DsachLoiView.copy_all_errors error: {e}")
                self._set_noti(f"Lỗi sao chép: {e}", is_error=True)

        self._page.run_task(_do_copy)

    @property
    def error_list(self) -> list[dict]:
        return self._errors

    def has_errors(self) -> bool:
        return len(self._errors) > 0

    # ------------------------------------------------------------------ #
    # Export
    # ------------------------------------------------------------------ #

    def _set_noti(self, message: str, is_error: bool = False):
        """Update _noti_text and refresh the parent Column so it appears."""
        self._noti_text.value = message
        self._noti_text.color = ft.Colors.ERROR if is_error else ft.Colors.SECONDARY
        self._noti_text.visible = bool(message)
        # Must update the Column (parent), not just the Text child
        self._safe_update()

    def _set_loading(self, loading: bool):
        self._export_btn.disabled = loading
        self._export_loading.visible = loading
        self._safe_update()

    def _export_to_excel(self):
        if not self._errors:
            self._set_noti("Không có lỗi để xuất")
            return

        def _do_export():
            self._set_loading(True)
            try:
                ret_excel_path = ExcelDsachLoiWriter().write_excel(data=self._errors)
                self._set_noti(f"✓ Đã xuất Excel: {ret_excel_path}")
            except Exception as e:
                LoggerUtil.get_logger().error(f"DsachLoiView._export_to_excel error: {e}")
                self._set_noti(f"Lỗi xuất Excel: {e}", is_error=True)
            finally:
                self._set_loading(False)

        self._page.run_thread(_do_export)