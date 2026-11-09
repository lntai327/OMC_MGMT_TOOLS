import traceback
import flet as ft
from functools import wraps

from share.util.logger_util import LoggerUtil

class DialogNoti:
    @staticmethod
    def show_error(page: ft.Page, message: str):
        def close_dialog(dlg: ft.AlertDialog):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Text("Lỗi"),
            content=ft.Text(message),
            actions=[
                ft.TextButton(
                    "OK",
                    on_click=lambda e: close_dialog(dlg),
                )
            ],
        )

        if dlg not in page.overlay:
            page.overlay.append(dlg)
        dlg.open = True
        page.update()

    @staticmethod
    def show_exception(page: ft.Page, ex: str):
        traceback.print_exc()

        DialogNoti.show_error(
            page,
            str(ex),
        )

def safe_callback(page_getter):
    """
    page_getter:
        lambda self: self.page
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            try:
                return func(*args, **kwargs)

            except Exception as ex:
                LoggerUtil.get_logger().critical(
                    f"App error: {ex}"
                )
                page = page_getter(args[0])
                DialogNoti.show_exception(page, "Lỗi ứng dụng")

        return wrapper

    return decorator
