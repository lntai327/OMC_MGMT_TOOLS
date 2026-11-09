from __future__ import annotations
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Iterable
import flet as ft

from frontend.component.explorer_ui_util import ExplorerUiUtil


if TYPE_CHECKING:
    from frontend.routing.router import Router


class BasePage:
    """Base class for all Flet pages.

    Pages are plain Python objects whose build() method returns a Flet Control.
    The Router calls build() and mounts the result into ft.View.controls.
    Subclasses must implement build() and provide a `title` class attribute.
    """
    title: str = ""
    show_back_button: bool = True
    vertical_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.START
    scroll: ft.ScrollMode | None = ft.ScrollMode.AUTO

    def __init__(self, page: ft.Page, router: "Router"):
        self.page = page
        self.router = router
        self.appbar: ft.AppBar | None = None
        self.back_button: ft.Control | None = None
        self.logout_button: ft.Control | None = None
        self.view: ft.View | None = None
        self._disabled_control_states: dict[int, bool] = {}

    @abstractmethod
    def build(self) -> ft.Control:
        ...

    def show_snack(self, message: str, error: bool = False):
        # LoggerUtil.get_logger().debug(f"show_snack: {message}")
        """Show a brief notification at the bottom of the screen."""
        snack = ft.SnackBar(
            content=ft.Text(message),
            # bgcolor=ft.Colors.ERROR_CONTAINER if error else None,
            open=True,
        )
        if hasattr(self.page, "open"):
            self.page.open(snack)
        else:
            self.page.overlay.append(snack)
            self.page.update()

    def show_dialog(
        self,
        title: str,
        message: str,
        width: int = 400,
        path: str | Path | None = None,
    ):
        """Show a notification dialog, optionally with an action to reveal a result path."""
        actions = []
        if path is not None and str(path) != "":
            actions.append(
                ft.TextButton(
                    "Mở",
                    on_click=lambda _: (
                        self._open_result_folder(path),
                        # self._close_dialog(dlg),
                    ),
                )
            )
        actions.append(ft.TextButton("Đóng", on_click=lambda _: self._close_dialog(dlg)))

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Text(message),
                width=width,
            ),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _close_dialog(self, dlg: ft.AlertDialog):
        dlg.open = False
        self.page.update()

    def _open_result_folder(self, path: str | Path):
        """Open the result path in the system file explorer."""
        ExplorerUiUtil().show_in_explorer(str(path))

    def set_controls_disabled(
        self,
        root: ft.Control,
        disabled: bool,
        exclude: Iterable[ft.Control] = (),
    ):
        """Disable or restore root container and navigation buttons."""
        try:
            if root is not None:
                root.disabled = disabled
        except Exception:
            pass

        try:
            if self.back_button is not None:
                self.back_button.disabled = disabled
        except Exception:
            pass

        try:
            if self.logout_button is not None:
                self.logout_button.disabled = disabled
        except Exception:
            pass
