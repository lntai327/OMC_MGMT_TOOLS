from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Iterable

import flet as ft

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
        self._disabled_control_states: dict[int, bool] = {}

    @abstractmethod
    def build(self) -> ft.Control:
        ...

    def show_snack(self, message: str, error: bool = False):
        """Show a brief notification at the bottom of the screen."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.ERROR_CONTAINER if error else None,
            open=True,
        )
        self.page.update()

    def show_dialog(self, title: str, message: str):
        """Show a simple info/error dialog."""
        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=lambda _: self._close_dialog(dlg))],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _close_dialog(self, dlg: ft.AlertDialog):
        dlg.open = False
        self.page.update()

    def set_controls_disabled(
        self,
        root: ft.Control,
        disabled: bool,
        exclude: Iterable[ft.Control] = (),
    ):
        """Disable or restore every disable-capable control below root."""
        excluded_ids = {id(control) for control in exclude}
        for control in self._walk_controls(root):
            if id(control) in excluded_ids or not hasattr(control, "disabled"):
                continue

            control_id = id(control)
            try:
                if disabled:
                    if control_id not in self._disabled_control_states:
                        self._disabled_control_states[control_id] = bool(control.disabled)
                    control.disabled = True
                elif control_id in self._disabled_control_states:
                    control.disabled = self._disabled_control_states.pop(control_id)
            except Exception:
                pass

    def _walk_controls(self, control: ft.Control):
        yield control

        content = getattr(control, "content", None)
        if isinstance(content, ft.Control):
            yield from self._walk_controls(content)

        controls = getattr(control, "controls", None)
        if controls:
            for child in controls:
                if isinstance(child, ft.Control):
                    yield from self._walk_controls(child)
