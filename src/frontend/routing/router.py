"""router.py — Flet page.views-based navigation router."""
from __future__ import annotations
from typing import TYPE_CHECKING

import flet as ft

from share.session import Session
from share.util.logger_util import LoggerUtil

if TYPE_CHECKING:
    from frontend.pages.base_page import BasePage


class Router:
    """Stack-based navigation router using Flet's page.views.

    Usage:
        router = Router(page)
        router.go("db_config")
        router.go_back()
    """

    # Route key → page class (populated by app.py)
    _routes: dict = {}

    def __init__(self, page: ft.Page):
        self._page = page
        self._history: list[str] = []  # stack of route keys

    def register_routes(self, routes: dict) -> None:
        """Register the route map: { "login": LoginPage, ... }"""
        Router._routes = routes

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #

    def _run_on_loop(self, fn, *args, **kwargs) -> None:
        """Ensure fn is executed on the page's main asyncio event loop."""
        try:
            import asyncio
            asyncio.get_running_loop()
            fn(*args, **kwargs)
        except RuntimeError:
            try:
                loop = self._page.session.connection.loop
                loop.call_soon_threadsafe(fn, *args, **kwargs)
            except Exception as e:
                LoggerUtil.get_logger().error(f"Router._run_on_loop error: {e}")

    def go(self, route_key: str, **kwargs) -> None:
        """Navigate to a named route, pushing it on the history stack."""
        self._run_on_loop(self._go_internal, route_key, **kwargs)

    def _go_internal(self, route_key: str, **kwargs) -> None:
        page_cls = Router._routes.get(route_key)
        if page_cls is None:
            LoggerUtil.get_logger().error(f"Router.go: unknown route '{route_key}'")
            return

        page_instance: BasePage = page_cls(self._page, self, **kwargs)
        try:
            control = page_instance.build()
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"Router.go: error building page '{route_key}': {e}")
            control = ft.Text(f"Ứng dụng lỗi!")

        appbar = self._build_appbar(page_instance, route_key)

        view = ft.View(
            route=f"/{route_key}",
            controls=[control],
            appbar=appbar,
            padding=0,
            vertical_alignment=getattr(
                page_instance, "vertical_alignment",
                ft.MainAxisAlignment.START),
            horizontal_alignment=getattr(
                page_instance, "horizontal_alignment",
                ft.CrossAxisAlignment.START),
            scroll=getattr(page_instance, "scroll", ft.ScrollMode.AUTO),
        )

        view.page_instance = page_instance
        page_instance.view = view

        self._page.views.append(view)
        self._history.append(route_key)
        self._page.go(f"/{route_key}")
        # LoggerUtil.get_logger().debug(f"Router.go → {route_key}")

    def go_back(self) -> None:
        """Pop the current view and return to the previous one."""
        def _do_go_back():
            if len(self._page.views) <= 1:
                return
            top_view = self._page.views[-1]
            page_instance = getattr(top_view, "page_instance", None)
            if page_instance and page_instance.back_button and getattr(page_instance.back_button, "disabled", False):
                return
            self._page.views.pop()
            if self._history:
                self._history.pop()
            top_view = self._page.views[-1]
            self._page.go(top_view.route)

        self._run_on_loop(_do_go_back)

    def replace(self, route_key: str, **kwargs) -> None:
        """Replace the current view (no back history entry added)."""
        def _do_replace():
            if self._page.views:
                self._page.views.pop()
                if self._history:
                    self._history.pop()
            self._go_internal(route_key, **kwargs)

        self._run_on_loop(_do_replace)

    def logout(self) -> None:
        """Log out the current user, clear session, and navigate to the login page."""
        def _do_logout():
            if len(self._page.views) >= 1:
                top_view = self._page.views[-1]
                page_instance = getattr(top_view, "page_instance", None)
                if page_instance \
                        and page_instance.logout_button \
                        and getattr(page_instance.logout_button, "disabled", False):
                    return

            Session.clear()
            self._history.clear()
            self._page.views.clear()
            self._go_internal("login")

        self._run_on_loop(_do_logout)

    # ------------------------------------------------------------------ #
    # AppBar
    # ------------------------------------------------------------------ #

    def _build_appbar(self, page_instance: BasePage, route_key: str) -> ft.AppBar:
        show_back = page_instance.show_back_button and len(self._history) > 0

        leading = (
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                tooltip="Quay lại",
                on_click=lambda _: self.go_back(),
            )
            if show_back
            else None
        )

        role: str = Session.get_role()
        if role != "":
            role = f" ({role})"
        title: str = (
            f"{page_instance.title}"
            f"{role}"
        )

        actions = []
        logout_btn = None
        if route_key != "login" and Session.is_logged_in():
            logout_btn = ft.TextButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.LOGOUT, size=18),
                        ft.Text("Đăng Xuất"),
                    ],
                    spacing=4,
                ),
                on_click=lambda _: self.logout(),
                tooltip="Đăng Xuất",
            )
            actions.append(logout_btn)

        appbar = ft.AppBar(
            leading=leading,
            leading_width=48,
            automatically_imply_leading=False,
            title=ft.Text(title, size=15, weight=ft.FontWeight.W_600),
            center_title=False,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            actions=actions,
        )

        page_instance.appbar = appbar
        page_instance.back_button = leading
        page_instance.logout_button = logout_btn

        return appbar
