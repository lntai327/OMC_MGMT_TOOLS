from __future__ import annotations
from datetime import date, datetime
from typing import Literal

import flet as ft

from frontend.component.custom_calendar import CalendarCustom
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.time_util import TimeUtil
from share.util.logger_util import LoggerUtil
from share.constant import constant as SC


_DATE_FORMAT = SC.K_DATETIME_FORMAT   # "%d/%m/%Y"


def _parse_date(s: str) -> date:
    try:
        return datetime.strptime(s, _DATE_FORMAT).date()
    except ValueError:
        return date.today()


def _fmt_date(d: date | datetime | str) -> str:
    if isinstance(d, datetime):
        return d.date().strftime(_DATE_FORMAT)
    if isinstance(d, date):
        return d.strftime(_DATE_FORMAT)
    if isinstance(d, str):
        try:
            dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
            return dt.date().strftime(_DATE_FORMAT)
        except Exception:
            return d
    return str(d)


class RpTimeControl(ft.Row):
    """Date picker control for report time selection.

    Modes:
        "single"   — one date field (rp_date)
        "from_to"  — two date fields (rp_time_from / rp_time_to)

    Each field shows a TextField + calendar IconButton that opens CalendarCustom.
    The selected date is persisted to DynamicInfoUtil automatically.
    """

    def __init__(self,
                 page: ft.Page,
                 mode: Literal["single", "from_to"] = "single"):
        self._page = page
        self._mode = mode
        self._calendar_dialog: ft.AlertDialog | None = None

        today = TimeUtil().get_current_time_str()

        # ------------------------------------------------------------------ #
        # From / single
        # ------------------------------------------------------------------ #
        self._from_field = ft.TextField(
            value=today, width=135, dense=True,
            read_only=False,
            on_blur=lambda _: self._on_from_typed(),
        )

        from_row = ft.Row([
            self._from_field,
            ft.IconButton(
                icon=ft.Icons.CALENDAR_TODAY,
                tooltip="Chọn ngày",
                on_click=lambda _: self._open_calendar(
                    _parse_date(self._from_field.value or today),
                    self._on_from_picked,
                ),
            ),
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        controls = [from_row]

        # ------------------------------------------------------------------ #
        # To (from_to mode only)
        # ------------------------------------------------------------------ #
        if mode == "from_to":
            self._to_field = ft.TextField(
                value=today, width=135, dense=True,
                read_only=False,
                on_blur=lambda _: self._on_to_typed(),
            )

            to_row = ft.Row([
                ft.Text("– ", size=14),
                self._to_field,
                ft.IconButton(
                    icon=ft.Icons.CALENDAR_TODAY,
                    tooltip="Chọn ngày",
                    on_click=lambda _: self._open_calendar(
                        _parse_date(self._to_field.value or today),
                        self._on_to_picked,
                    ),
                ),
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            controls.append(to_row)

        super().__init__(
            controls=controls, spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # persist initial values
        self._persist_from(today)
        if mode == "from_to":
            self._persist_to(today)

    def _open_calendar(self, selected_date: date, on_selected):
        if self._calendar_dialog in self._page.overlay:
            self._page.overlay.remove(self._calendar_dialog)

        calendar = CalendarCustom(
            on_date_selected=lambda selected: self._on_calendar_selected(
                selected, on_selected
            )
        )
        calendar.selected_date = selected_date
        calendar.current_display_date = selected_date

        self._calendar_dialog = ft.AlertDialog(
            modal=False,
            content=calendar,
            actions=[
                ft.TextButton("Đóng", on_click=lambda _: self._close_calendar()),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        self._page.overlay.append(self._calendar_dialog)
        self._calendar_dialog.open = True
        self._page.update()

    def _on_calendar_selected(self, selected_date: date, on_selected):
        on_selected(selected_date)

    def _close_calendar(self):
        if self._calendar_dialog is None:
            return
        self._calendar_dialog.open = False
        self._page.update()

    # ------------------------------------------------------------------ #
    # Public properties
    # ------------------------------------------------------------------ #

    @property
    def date_from(self) -> str:
        return self._from_field.value or ""

    @property
    def date_to(self) -> str:
        if self._mode == "from_to":
            return self._to_field.value or ""
        return ""

    @property
    def date_single(self) -> str:
        return self._from_field.value or ""

    # ------------------------------------------------------------------ #
    # Handlers — from
    # ------------------------------------------------------------------ #

    def _on_from_picked(self, selected_date: date):
        s = _fmt_date(selected_date)
        self._from_field.value = s
        self._from_field.update()
        self._persist_from(s)

    def _on_from_typed(self):
        s = self._from_field.value or ""
        self._persist_from(s)

    def _persist_from(self, s: str):
        try:
            if self._mode == "single":
                DynamicInfoUtil().set_value(
                    s, 2, SC.K_SCREEN_INPUT, SC.K_RP_DATE)
            else:
                DynamicInfoUtil().set_value(
                    s, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_FROM)
        except Exception as e:
            LoggerUtil.get_logger().error(f"RpTimeControl._persist_from error: {e}")

    # ------------------------------------------------------------------ #
    # Handlers — to (from_to mode)
    # ------------------------------------------------------------------ #

    def _on_to_picked(self, selected_date: date):
        s = _fmt_date(selected_date)
        self._to_field.value = s
        self._to_field.update()
        self._persist_to(s)

    def _on_to_typed(self):
        s = self._to_field.value or ""
        self._persist_to(s)

    def _persist_to(self, s: str):
        try:
            DynamicInfoUtil().set_value(s, 2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TO)
        except Exception as e:
            LoggerUtil.get_logger().error(f"RpTimeControl._persist_to error: {e}")
