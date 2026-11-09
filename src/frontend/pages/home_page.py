import flet as ft

from frontend.pages.base_page import BasePage
from frontend.viewmodels.home_vm import HomeViewModel
from share.constant import constant as SC


class HomePage(BasePage):
    title = "Chọn Loại Báo Cáo"
    show_back_button = False

    def __init__(self, page: ft.Page, router, **kwargs):
        super().__init__(page, router)
        self._vm = HomeViewModel()
        self._vm.subscribe("filtered_reports", self._on_filter_changed)

    # ------------------------------------------------------------------ #
    # Build
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        self._search_field = ft.TextField(
            label=SC.K_UI_REPORT_TYPE,
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda e: self._vm.update_filter(e.control.value),
            on_submit=lambda _: self._select_top(),
            dense=True,
            expand=True,
        )

        self._list_view = ft.ListView(spacing=4, expand=True)
        self._rebuild_list()

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "OMC Report Tool",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    ),
                    ft.Divider(),
                    ft.Row([self._search_field]),
                    ft.Container(
                        content=self._list_view,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                        border_radius=8,
                        padding=4,
                        height=450,
                    )
                ],
                spacing=12,
            ),
            padding=ft.Padding.all(24),
            expand=True,
        )

    # ------------------------------------------------------------------ #
    # VM subscriber
    # ------------------------------------------------------------------ #

    def _on_filter_changed(self):
        self._rebuild_list()
        try:
            self._list_view.update()
        except Exception:
            pass

    def _rebuild_list(self):
        self._list_view.controls.clear()
        for name in self._vm.filtered_reports:
            tile = ft.ListTile(
                title=ft.Text(name, size=13),
                leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED),
                on_click=lambda _, n=name: self._navigate_to(n),
                selected=False,
            )
            self._list_view.controls.append(tile)

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #

    def _select_top(self):
        reports = self._vm.filtered_reports
        if not reports:
            return
        self._navigate_to(reports[0])

    def _navigate_to(self, report_name: str):
        route = self._vm.get_route_for_report(report_name)
        if route:
            self.router.go(route)