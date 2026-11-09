import re
from typing import Dict, Optional
import flet as ft

from frontend.component.common_view import safe_callback
from frontend.component.explorer_ui_util import ExplorerUiUtil
from frontend.component.loading_overlay import LoadingOverlay
from frontend.component.update_db_dialog import UpdateDbDialog
import frontend.constant.type as FET
from frontend.pages.base_page import BasePage
from frontend.viewmodels.megawan_metronet_vm import MegawanMetronetViewModel
from share.constant import constant as SC
from share.session import Session
from share.util.logger_util import LoggerUtil


class MegawanMetronetPage(BasePage):
    title = FET.ReportTypeInfo.QLY_MEGAWAN.report_name
    scroll = None

    def __init__(self, page: ft.Page, router, **kwargs):
        super().__init__(page, router)
        self._vm = MegawanMetronetViewModel()
        self._vm.subscribe("is_loading", self._on_loading)
        self._vm.subscribe("data_changed", self._on_data_changed)
        self._vm.subscribe("status_changed", self._on_status_changed)
        self._vm.subscribe("selected_record_changed", self._on_selected_record_changed)

        self._explorer_util = ExplorerUiUtil()
        self._explorer_util.register(page)

        self._is_admin = Session.is_admin()
        self._file_picker = ft.FilePicker()

        self._min_col_width: float = 40
        self._col_spacing: float = 4
        self._header_cells: Dict[str, ft.Container] = {}

        # Default fixed column widths
        self._col_widths: Dict[str, float] = {
            SC.K_STT: 50,
            SC.K_LAST_UPDATE: 110,
            SC.K_MA_TB: 110,
            SC.K_MA_LT_MA_TB_SUB: 110,
            SC.K_TEN_TH_BAO: 180,
            SC.K_DIA_CHI: 200,
            SC.K_ID: 50,
            SC.K_DIEM_CUOI: 150,
            SC.K_IP_SRC: 110,
            SC.K_IP_DES: 110,
            SC.K_SVLAN_CVLAN: 120,
            SC.K_CAP_ADSL: 100,
            SC.K_CAP_ODF: 100,
            SC.K_GHI_CHU: 180,
            SC.K_IP: 100,
            SC.K_TEN_HE_THONG: 95,
            SC.K_PORT_SWITCH: 95,
            SC.K_UPE: 80,
            SC.K_LOAI_HINH_TB: 110,
            SC.K_TRANG_THAI: 90,
            SC.K_TOC_DO: 90,
            SC.K_DVI: 130,
            SC.K_LOAI_KENH: 130,

            "thao_tac": 75,
        }

        self._table_col_keys = [
            SC.K_STT,
            SC.K_LAST_UPDATE,
            SC.K_MA_TB,
            SC.K_MA_LT_MA_TB_SUB,
            SC.K_TEN_TH_BAO,
            SC.K_DIA_CHI,
            SC.K_ID,
            SC.K_DIEM_CUOI,
            SC.K_IP_SRC,
            SC.K_IP_DES,
            SC.K_SVLAN_CVLAN,
            SC.K_CAP_ADSL,
            SC.K_CAP_ODF,
            SC.K_GHI_CHU,
            SC.K_IP,
            SC.K_TEN_HE_THONG,
            SC.K_PORT_SWITCH,
            SC.K_UPE,
            SC.K_LOAI_HINH_TB,
            SC.K_TRANG_THAI,
            SC.K_TOC_DO,
            SC.K_DVI,
            SC.K_LOAI_KENH,

            "thao_tac",
        ]

        self._col_labels: Dict[str, str] = {
            SC.K_STT: "STT",
            SC.K_MA_TB: "MÃ TB",
            SC.K_MA_LT_MA_TB_SUB: "MÃ LT/MÃ TB SUB",
            SC.K_TEN_TH_BAO: "Tên thuê bao",
            SC.K_DIA_CHI: "Địa chỉ lắp đặt",
            SC.K_ID: "id",
            SC.K_DIEM_CUOI: "Điểm cuối",
            SC.K_IP_SRC: "IP Nguồn",
            SC.K_IP_DES: "IP Đích",
            SC.K_SVLAN_CVLAN: "SVLAN/CVLAN",
            SC.K_CAP_ADSL: "Cáp ADSL",
            SC.K_CAP_ODF: "Cáp ODF",
            SC.K_LAST_UPDATE: "Cập nhật lần cuối",
            SC.K_GHI_CHU: "Ghi chú",
            SC.K_IP: "ip",
            SC.K_TEN_HE_THONG: "Tên hệ thống",
            SC.K_PORT_SWITCH: "Port SWITCH",
            SC.K_UPE: "UPE",
            SC.K_LOAI_HINH_TB: "LOẠI HÌNH TB",
            SC.K_TRANG_THAI: "Trạng thái",
            SC.K_TOC_DO: "Tốc độ",
            SC.K_DVI: "Đơn vị",
            SC.K_LOAI_KENH: "Loại kênh",

            "thao_tac": "Thao tác",
        }

        # Form dialog fields for create / edit
        self._form_fields: Dict[str, ft.Control] = {}
        self._current_edit_record_id: Optional[int] = None
        self._current_delete_record: Optional[dict] = None
        self._update_db_dialog: Optional[UpdateDbDialog] = None

    # ------------------------------------------------------------------
    # Build Page
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        if self._file_picker not in self.page.services:
            self.page.services.append(self._file_picker)

        self._overlay = LoadingOverlay()

        # --- Top Action Bar ---
        top_bar = self._build_top_bar()

        # --- Search / Filter Area ---
        filter_area = self._build_filter_area()

        # --- Table Section ---
        table_section = self._build_table_section()

        # --- Pagination Bar ---
        pagination_bar = self._build_pagination_bar()

        # --- In-Page Detail Section ---
        detail_record_section = self._build_detail_record_section()

        # Build Form Dialog for Create & Edit
        self._record_form_dialog = self._build_record_form_dialog()
        # Build Delete Confirmation Dialog
        self._delete_record_dialog = self._build_delete_dialog()

        self.page.overlay.extend(
            [self._record_form_dialog, self._delete_record_dialog]
        )

        # Main scrollable/organized layout
        main_layout = ft.Column(
            controls=[
                top_bar,
                filter_area,
                ft.Container(
                    content=table_section,
                    expand=True,
                ),
                pagination_bar,
                # detail_record_section, # TODO
            ],
            spacing=0,
            expand=True,
        )
        self._interactive_root = main_layout

        # Initial data load
        self._vm.load_in_background(self.page)

        return ft.Stack(
            controls=[
                main_layout,
                self._overlay,
            ],
            expand=True,
        )

    # ------------------------------------------------------------------
    # Section Builders
    # ------------------------------------------------------------------

    def _build_top_bar(self) -> ft.Container:
        btn_style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=ft.Padding.symmetric(horizontal=12, vertical=0),
        )

        buttons = [
            ft.FilledButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.ADD, size=16),
                        ft.Text("Thêm mới"),
                    ],
                    spacing=6,
                    tight=True,
                ),
                style=btn_style,
                height=34,
                on_click=lambda _: self._open_create_dialog(),
            ),
            ft.OutlinedButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.FILE_DOWNLOAD_OUTLINED, size=16),
                        ft.Text("Xuất Excel"),
                    ],
                    spacing=6,
                    tight=True,
                ),
                style=btn_style,
                height=34,
                on_click=lambda _: self._on_export_click(),
            ),
            ft.OutlinedButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.REFRESH, size=16),
                        ft.Text("Tải lại"),
                    ],
                    spacing=6,
                    tight=True,
                ),
                style=btn_style,
                height=34,
                on_click=lambda _: self._vm.load_in_background(self.page),
            ),
        ]

        if self._is_admin:
            buttons.append(
                ft.OutlinedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.STORAGE, size=16),
                            ft.Text("Cập nhật CSDL"),
                        ],
                        spacing=6,
                        tight=True,
                    ),
                    style=btn_style,
                    height=34,
                    on_click=lambda _: self._open_update_db_dialog(),
                )
            )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(controls=buttons, spacing=8),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    def _build_filter_area(self) -> ft.Container:
        # Search inputs according to requirement:
        # SC.K_LOAI_HINH_TB, SC.K_TEN_TH_BAO, SC.K_DIA_CHI,
        # SC.K_LOAI_KENH, SC.K_SVLAN_CVLAN, ALL
        self._filter_inputs: Dict[str, ft.TextField] = {
            SC.K_LOAI_HINH_TB: ft.TextField(
                label="LOẠI HÌNH TB",
                dense=True,
                height=38,
                expand=1,
                border_radius=6,
                on_submit=lambda _: self._on_search_click(),
            ),
            SC.K_TEN_TH_BAO: ft.TextField(
                label="Tên thuê bao",
                dense=True,
                height=38,
                expand=2,
                border_radius=6,
                on_submit=lambda _: self._on_search_click(),
            ),
            SC.K_DIA_CHI: ft.TextField(
                label="Địa chỉ",
                dense=True,
                height=38,
                expand=2,
                border_radius=6,
                on_submit=lambda _: self._on_search_click(),
            ),
            SC.K_LOAI_KENH: ft.TextField(
                label="Loại kênh",
                dense=True,
                height=38,
                expand=1,
                border_radius=6,
                on_submit=lambda _: self._on_search_click(),
            ),
            SC.K_SVLAN_CVLAN: ft.TextField(
                label="SVLAN / CVLAN",
                dense=True,
                height=38,
                expand=1,
                border_radius=6,
                on_submit=lambda _: self._on_search_click(),
            ),
            SC.K_TEN_HE_THONG: ft.TextField(
                label="Tên hệ thống",
                dense=True,
                height=38,
                expand=1,
                border_radius=6,
                on_submit=lambda _: self._on_search_click(),
            ),
            MegawanMetronetViewModel.ALL_KEY: ft.TextField(
                label="Tìm kiếm tất cả",
                dense=True,
                height=38,
                expand=2,
                border_radius=6,
                on_submit=lambda _: self._on_search_click(),
            ),
        }

        # Row 1: First 4 inputs
        row1 = ft.Row(
            controls=[
                self._filter_inputs[SC.K_LOAI_HINH_TB],
                self._filter_inputs[SC.K_TEN_TH_BAO],
                self._filter_inputs[SC.K_DIA_CHI],
            ],
            spacing=8,
        )

        # Row 2: Remaining inputs + Search & Reset Buttons
        row2 = ft.Row(
            controls=[
                self._filter_inputs[SC.K_LOAI_KENH],
                self._filter_inputs[SC.K_SVLAN_CVLAN],
                self._filter_inputs[SC.K_TEN_HE_THONG],
                self._filter_inputs[MegawanMetronetViewModel.ALL_KEY],
                ft.FilledButton(
                    content=ft.Row(
                        [ft.Icon(ft.Icons.SEARCH, size=16), ft.Text("Tìm kiếm")],
                        spacing=4,
                        tight=True,
                    ),
                    height=38,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                    on_click=lambda _: self._on_search_click(),
                ),
                ft.OutlinedButton(
                    content=ft.Row(
                        [ft.Icon(ft.Icons.CLEAR_ALL, size=16), ft.Text("Đặt lại")],
                        spacing=4,
                        tight=True,
                    ),
                    height=38,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                    on_click=lambda _: self._on_reset_filter_click(),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    row1,
                    row2,
                ],
                spacing=8,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    def _build_table_section(self) -> ft.Control:
        # Build resizable table header row
        self._header_row = self._build_header_row()

        self._header_container = ft.Container(
            content=self._header_row,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=ft.Padding.symmetric(horizontal=12, vertical=4),
            border_radius=ft.BorderRadius.only(top_left=6, top_right=6),
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            width=self._total_row_width(),
        )

        self._table_body_view = ft.ListView(controls=[], expand=True)

        self._empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.TABLE_ROWS_OUTLINED, size=48, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text("Chưa có bản ghi nào", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(vertical=40),
            visible=False,
        )

        self._table_inner_column = ft.Container(
            content=ft.Column(
                controls=[
                    self._header_container,
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                self._table_body_view,
                                self._empty_state,
                            ],
                            expand=True,
                        ),
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            width=self._total_row_width(),
        )

        table_scroll_row = ft.Row(
            controls=[self._table_inner_column],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        return table_scroll_row

    def _build_pagination_bar(self) -> ft.Container:
        self._page_size_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("20"),
                ft.dropdown.Option("50"),
                ft.dropdown.Option("100"),
                ft.dropdown.Option("500"),
            ],
            value=str(self._vm.page_size),
            width=90,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=6,
            dense=True,
            on_select=lambda e: self._vm.set_page_size(int(e.control.value)),
        )

        self._pagination_text = ft.Text("Trang 1 / 1 (Tổng: 0)", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._btn_prev_page = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_size=18,
            on_click=lambda _: self._vm.go_to_page(self._vm.current_page - 1),
        )
        self._btn_next_page = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_size=18,
            on_click=lambda _: self._vm.go_to_page(self._vm.current_page + 1),
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Hiển thị:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                            self._page_size_dropdown,
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(expand=True),
                    self._pagination_text,
                    self._btn_prev_page,
                    self._btn_next_page,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=4),
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
        )

    def _build_detail_record_section(self) -> ft.Container:
        self._detail_title = ft.Text(
            "Chi Tiết Bản Ghi",
            size=14,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.PRIMARY,
        )

        # Labels + value texts for all 18 fields
        self._detail_value_texts: Dict[str, ft.Text] = {}
        cards = []

        for col_key in [
            SC.K_LOAI_HINH_TB,
            SC.K_TEN_TH_BAO,
            SC.K_DIA_CHI,
            SC.K_LOAI_KENH,
            SC.K_SVLAN_CVLAN,
            SC.K_TEN_HE_THONG,
            SC.K_DIEM_CUOI,
            SC.K_IP_SRC,
            SC.K_IP_DES,
            SC.K_PORT_SWITCH,
            SC.K_TOC_DO,
            SC.K_CAP_ADSL,
            SC.K_CAP_ODF,
            SC.K_LAST_UPDATE,
            SC.K_GHI_CHU,
        ]:
            val_text = ft.Text("—", color=ft.Colors.ON_SURFACE, selectable=True)
            self._detail_value_texts[col_key] = val_text
            label = self._col_labels.get(col_key, col_key)

            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(label, color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.W_500),
                        val_text,
                    ],
                    spacing=2,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=6,
                bgcolor=ft.Colors.SURFACE,
                width=180,
            )
            cards.append(card)

        self._btn_detail_edit = ft.FilledButton(
            content=ft.Row([ft.Icon(ft.Icons.EDIT, size=14), ft.Text("Chỉnh sửa", size=12)], spacing=4, tight=True),
            height=30,
            visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
            on_click=lambda _: self._on_detail_edit_click(),
        )

        self._btn_detail_delete = ft.OutlinedButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.DELETE_OUTLINE, size=14, color=ft.Colors.ERROR), ft.Text("Xóa", size=12, color=ft.Colors.ERROR)],
                spacing=4,
                tight=True,
            ),
            height=30,
            visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
            on_click=lambda _: self._on_detail_delete_click(),
        )

        scrollable_cards = ft.Column(
            controls=[
                ft.Row(
                    controls=cards,
                    wrap=True,
                    spacing=8,
                    run_spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        detail_content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=ft.Colors.PRIMARY),
                        self._detail_title,
                        ft.Container(expand=True),
                        self._btn_detail_edit,
                        self._btn_detail_delete,
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=4),
                scrollable_cards,
            ],
            spacing=4,
            expand=True,
        )

        return ft.Container(
            content=detail_content,
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            height=250,
        )

    # ------------------------------------------------------------------
    # Table Widths & Resizing
    # ------------------------------------------------------------------

    def _total_row_width(self) -> float:
        n = len(self._table_col_keys)
        return sum(self._col_widths.get(k, 80) for k in self._table_col_keys) + self._col_spacing * (n - 1) + 24

    def _make_table_cell(self, content: ft.Control, col_key: str) -> ft.Container:
        width = self._col_widths.get(col_key, self._min_col_width)
        align = ft.Alignment.CENTER if col_key in (SC.K_STT, "thao_tac") else ft.Alignment.CENTER_LEFT
        return ft.Container(
            content=content,
            width=width,
            alignment=align,
            border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.symmetric(horizontal=4),
        )

    def _make_resizable_header_cell(self, label_text: str, col_key: str, height: float = 38) -> ft.Container:
        width = self._col_widths.get(col_key, self._min_col_width)
        align = ft.Alignment.CENTER

        divider = ft.GestureDetector(
            content=ft.Container(width=6, height=height, ink=True),
            mouse_cursor=ft.MouseCursor.RESIZE_COLUMN,
            drag_interval=10,
            on_horizontal_drag_update=lambda e, _k=col_key: self._on_col_resize(e, _k),
        )

        cell = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            label_text,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        expand=True,
                        alignment=align,
                        padding=ft.Padding.symmetric(horizontal=2),
                    ),
                    divider,
                ],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=width,
            height=height,
            border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )
        return cell

    def _build_header_row(self) -> ft.Row:
        self._header_cells.clear()
        outer_cells = []
        for col_key in self._table_col_keys:
            label = self._col_labels.get(col_key, col_key)
            cell = self._make_resizable_header_cell(label, col_key)
            self._header_cells[col_key] = cell
            outer_cells.append(cell)

        return ft.Row(
            controls=outer_cells,
            spacing=self._col_spacing,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _on_col_resize(self, e: ft.DragUpdateEvent, col_key: str):
        new_width = self._col_widths.get(col_key, 80) + (e.primary_delta or 0)
        if new_width < self._min_col_width:
            new_width = self._min_col_width
        self._col_widths[col_key] = new_width
        self._rebuild_table_widths()

    def _rebuild_table_widths(self):
        total_w = self._total_row_width()

        for col_key, cell_container in self._header_cells.items():
            cell_container.width = self._col_widths.get(col_key, self._min_col_width)

        if hasattr(self, "_header_container") and self._header_container:
            self._header_container.width = total_w
        if hasattr(self, "_table_inner_column") and self._table_inner_column:
            self._table_inner_column.width = total_w

        if hasattr(self, "_table_body_view") and self._table_body_view:
            for row_container in self._table_body_view.controls:
                if not isinstance(row_container, ft.Container):
                    continue
                row_ctrl = row_container.content
                if not isinstance(row_ctrl, ft.Row):
                    continue
                for body_cell, col_key in zip(row_ctrl.controls, self._table_col_keys):
                    body_cell.width = self._col_widths.get(col_key, self._min_col_width)
                row_container.width = total_w

        try:
            self.page.update()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # CRUD Dialogs
    # ------------------------------------------------------------------

    def _build_record_form_dialog(self) -> ft.AlertDialog:
        self._form_fields.clear()

        lbl_w_left = 115
        lbl_w_right = 115

        def _make_tf(
            expand: bool = True,
            multiline: bool = False,
            min_lines: int = 1, max_lines: int = 1,
            content_padding = None,
        ) -> ft.TextField:
            return ft.TextField(
                dense=True,
                expand=expand,
                border_radius=6,
                multiline=multiline,
                min_lines=min_lines,
                max_lines=max_lines,
                content_padding=content_padding,
            )

        def _field_row_full(
            label_text: str,
            control: ft.Control,
            align_top: bool = False
        ) -> ft.Row:
            return ft.Row(
                [
                    ft.Container(
                        content=ft.Text(label_text),
                        width=lbl_w_left,
                        alignment=ft.Alignment(-1, -1 if align_top else 0),
                        padding=ft.Padding(0, 8 if align_top else 0, 0, 0),
                    ),
                    control,
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START if align_top else ft.CrossAxisAlignment.CENTER,
            )

        def _field_row_2col(
            lbl1: str, ctrl1: ft.Control,
            lbl2: str, ctrl2: ft.Control,
        ) -> ft.Row:
            col1 = ft.Row(
                [
                    ft.Container(
                        content=ft.Text(lbl1),
                        width=lbl_w_left,
                        alignment=ft.Alignment(-1, 0),
                    ),
                    ctrl1,
                ],
                spacing=10,
                expand=1,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            col2 = ft.Row(
                [
                    ft.Container(
                        content=ft.Text(lbl2),
                        width=lbl_w_right,
                        alignment=ft.Alignment(-1, 0),
                    ),
                    ctrl2,
                ],
                spacing=10,
                expand=1,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            return ft.Row([col1, col2], spacing=16)

        # Dịch vụ (Dropdown, compact width)
        dd_loai_dg_truyen = ft.Dropdown(
                dense=True,
                expand=False,
                width=200,
                border_radius=6,
                options=[
                    ft.dropdown.Option("megawan_metronet"),
                    ft.dropdown.Option("metronet"),
                ],
            )
        self._form_fields[SC.K_LOAI_HINH_TB] = dd_loai_dg_truyen
        row_dich_vu = ft.Row(
            [
                ft.Container(
                    content=ft.Text(f"{self._col_labels.get(SC.K_LOAI_HINH_TB)}:"),
                    width=lbl_w_left,
                    alignment=ft.Alignment(-1, 0),
                ),
                dd_loai_dg_truyen,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Tên khách hàng (Full width TextField)
        tf_kh = _make_tf(expand=True)
        self._form_fields[SC.K_TEN_TH_BAO] = tf_kh
        row_kh = _field_row_full(f"{self._col_labels.get(SC.K_TEN_TH_BAO)}:", tf_kh)

        # Địa chỉ (Full width TextField)
        tf_dc = _make_tf(expand=True)
        self._form_fields[SC.K_DIA_CHI] = tf_dc
        row_dc = _field_row_full("Địa chỉ:", tf_dc)

        # Điểm cuối (Full width TextField)
        tf_dc_cuoi = _make_tf(expand=True)
        self._form_fields[SC.K_DIEM_CUOI] = tf_dc_cuoi
        row_dc_cuoi = _field_row_full(f"{self._col_labels.get(SC.K_DIEM_CUOI)}:", tf_dc_cuoi)

        # Loại cáp & Loại kênh (2 columns Dropdown)
        dd_loai_kenh = ft.Dropdown(
            dense=True,
            expand=True,
            width=None,
            border_radius=6,
            options=[
                ft.dropdown.Option("Liên tỉnh"),
                ft.dropdown.Option("Nội hạt"),
            ],
        )
        self._form_fields[SC.K_LOAI_KENH] = dd_loai_kenh
        row_cap_kenh = _field_row_full(f"{self._col_labels.get(SC.K_LOAI_KENH)}:", dd_loai_kenh)

        # IP nguồn & IP đích (2 columns TextField)
        tf_ip_src = _make_tf(expand=True)
        tf_ip_des = _make_tf(expand=True)
        self._form_fields[SC.K_IP_SRC] = tf_ip_src
        self._form_fields[SC.K_IP_DES] = tf_ip_des
        row_ip = _field_row_2col(
            f"{self._col_labels.get(SC.K_IP_SRC)}:", tf_ip_src,
            f"{self._col_labels.get(SC.K_IP_DES)}:", tf_ip_des
        )

        # Switch/OLT & Frame/Slot/Port (2 columns TextField)
        tf_switch = _make_tf(expand=True)
        self._form_fields[SC.K_TEN_HE_THONG] = tf_switch
        row_switch_fsp = _field_row_full(
            f"{self._col_labels.get(SC.K_TEN_HE_THONG)}:", tf_switch
        )

        # SVlan/CVlan
        tf_vlan = _make_tf(expand=True)
        self._form_fields[SC.K_SVLAN_CVLAN] = tf_vlan
        row_svlan_cvlan = _field_row_full(
            f"{self._col_labels.get(SC.K_SVLAN_CVLAN)}:", tf_vlan
        )

        # Tốc độ & đơn vị (2 columns: input TextField & dropdown speed type M/K)
        tf_toc_do = _make_tf(
            expand=3,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=16),
        )
        self._form_fields[SC.K_TOC_DO] = tf_toc_do

        dd_toc_do_dvi = ft.Dropdown(
            dense=True,
            expand=1,
            border_radius=6,
            value="M",
            options=[
                ft.dropdown.Option("M"),
                ft.dropdown.Option("K"),
            ],
        )
        self._form_fields[SC.K_DVI] = dd_toc_do_dvi

        row_toc_do_va_dvi = _field_row_full(
            "Tốc độ:",
            ft.Row(
                [
                    tf_toc_do,
                    dd_toc_do_dvi,
                ],
                spacing=10,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Cáp ADSL/Port & Cáp MDF (2 columns TextField)
        tf_adsl = _make_tf(expand=True)
        tf_odf = _make_tf(expand=True)
        self._form_fields[SC.K_CAP_ADSL] = tf_adsl
        self._form_fields[SC.K_CAP_ODF] = tf_odf
        row_adsl_mdf = _field_row_2col(
            f"{self._col_labels.get(SC.K_CAP_ADSL)}:", tf_adsl,
            f"{self._col_labels.get(SC.K_CAP_ODF)}:", tf_odf
        )

        # Ghi chú (Multiline TextField)
        tf_ghi_chu = _make_tf(expand=True, multiline=True, min_lines=4, max_lines=6)
        self._form_fields[SC.K_GHI_CHU] = tf_ghi_chu
        row_ghi_chu = _field_row_full(
            f"{self._col_labels.get(SC.K_GHI_CHU)}:", tf_ghi_chu, align_top=True
        )

        form_rows = [
            row_dich_vu,
            row_kh,
            row_dc,
            row_dc_cuoi,
            row_cap_kenh,
            row_ip,
            row_switch_fsp,
            row_svlan_cvlan,
            row_toc_do_va_dvi,
            row_adsl_mdf,
            row_ghi_chu,
        ]

        self._record_dialog_title = ft.Text(
            "Thêm Mới Bản Ghi", weight=ft.FontWeight.W_600
        )

        return ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.EDIT_DOCUMENT, color=ft.Colors.PRIMARY, size=22),
                    self._record_dialog_title,
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=form_rows,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    tight=True,
                ),
                width=750,
                height=650,
                padding=ft.Padding.all(8),
            ),
            actions=[
                ft.TextButton("Hủy", on_click=lambda _: self._close_record_form_dialog()),
                ft.FilledButton("Lưu", on_click=lambda _: self._save_record_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

    def _open_create_dialog(self):
        self._current_edit_record_id = None
        self._record_dialog_title.value = "Thêm Mới Bản Ghi"
        for ctrl in self._form_fields.values():
            ctrl.value = ""
        if SC.K_DVI in self._form_fields:
            self._form_fields[SC.K_DVI].value = "M"
        self._record_form_dialog.open = True
        self.page.update()

    def _open_edit_dialog(self, record: dict):
        self._current_edit_record_id = record.get(SC.K_ID)
        self._record_dialog_title.value = "Chỉnh Sửa Bản Ghi"
        for k, ctrl in self._form_fields.items():
            val = str(record.get(k, "") or "")
            if isinstance(ctrl, ft.Dropdown):
                if val:
                    existing_keys = [opt.key if opt.key is not None else opt.text for opt in ctrl.options]
                    if val not in existing_keys:
                        ctrl.options.append(ft.dropdown.Option(val))
                    ctrl.value = val
                else:
                    ctrl.value = None
            else:
                ctrl.value = val
        self._record_form_dialog.open = True
        self.page.update()

    def _close_record_form_dialog(self):
        self._record_form_dialog.open = False
        self.page.update()

    def _save_record_dialog(self):
        payload = {k: ctrl.value or "" for k, ctrl in self._form_fields.items()}
        self._close_record_form_dialog()

        if self._current_edit_record_id is not None:
            self.page.run_thread(lambda: self._vm.update_record(self._current_edit_record_id, payload))
        else:
            self.page.run_thread(lambda: self._vm.create_record(payload))

    def _build_delete_dialog(self) -> ft.AlertDialog:
        return ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.ERROR, size=24),
                    ft.Text("Xác Nhận Xóa", weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            actions=[
                ft.TextButton("Hủy", on_click=lambda _: self._close_delete_dialog()),
                ft.FilledButton(
                    "Xóa",
                    style=ft.ButtonStyle(bgcolor=ft.Colors.ERROR),
                    on_click=lambda _: self._confirm_delete(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

    def _open_delete_dialog(self, record: dict):
        self._current_delete_record = record
        self._delete_record_dialog.open = True
        self.page.update()

    def _close_delete_dialog(self):
        self._delete_record_dialog.open = False
        self._current_delete_record = None
        self.page.update()

    def _confirm_delete(self):
        rec = self._current_delete_record
        self._close_delete_dialog()
        if rec and rec.get(SC.K_ID):
            rec_id = rec.get(SC.K_ID)
            self.page.run_thread(lambda: self._vm.delete_record(rec_id))

    def _open_update_db_dialog(self):
        if self._update_db_dialog is None:
            self._update_db_dialog = UpdateDbDialog(
                self.page,
                self._vm.get_db_update_list(),
                on_db_updated=lambda: self._vm.load_in_background(self.page),
            )
        self._update_db_dialog.open()

    # ------------------------------------------------------------------
    # Actions & Event Handlers
    # ------------------------------------------------------------------

    @safe_callback(lambda self: self.page)
    def _on_search_click(self):
        filter_vals = {k: tf.value or "" for k, tf in self._filter_inputs.items()}
        self._vm.apply_filters(filter_vals)

    @safe_callback(lambda self: self.page)
    def _on_reset_filter_click(self):
        for tf in self._filter_inputs.values():
            tf.value = ""
        self._vm.reset_filters()
        self.page.update()

    @safe_callback(lambda self: self.page)
    def _on_export_click(self):
        async def _async_export():
            folder_path = await self._file_picker.get_directory_path(
                dialog_title="Chọn thư mục xuất dữ liệu",
            )
            if folder_path:
                self.page.run_thread(lambda: self._vm.export_to_excel(folder_path))

        self.page.run_task(_async_export)

    def _on_detail_edit_click(self):
        sel = self._vm.selected_record
        if sel:
            self._open_edit_dialog(sel)

    def _on_detail_delete_click(self):
        sel = self._vm.selected_record
        if sel:
            self._open_delete_dialog(sel)

    # ------------------------------------------------------------------
    # VM Subscribers & UI Sync
    # ------------------------------------------------------------------

    def _on_loading(self):
        loading = self._vm.is_loading

        async def _apply():
            try:
                if loading:
                    self._overlay.show()
                else:
                    self._overlay.hide()
                self.set_controls_disabled(self._interactive_root, loading)
                self.page.update()
            except Exception as e:
                LoggerUtil.get_logger().error(f"MegawanMetronetPage _on_loading error: {e}")

        try:
            self.page.run_task(_apply)
        except Exception:
            pass

    def _on_status_changed(self):
        async def _apply():
            try:
                if self._vm.error_message:
                    self.show_dialog("Lỗi", self._vm.error_message)
                elif self._vm.success_message:
                    self.show_dialog(
                        title="Thông báo",
                        message=self._vm.success_message,
                        path=self._vm.path_message,
                    )
            except Exception as e:
                LoggerUtil.get_logger().error(f"MegawanMetronetPage _on_status_changed error: {e}")

        try:
            self.page.run_task(_apply)
        except Exception:
            pass

    def _on_data_changed(self):
        async def _apply():
            try:
                self._page_size_dropdown.value = str(self._vm.page_size)
                items = self._vm.paginated_records
                total_items = self._vm.total_records_count

                rows = []
                selected_id = self._vm.selected_record.get(SC.K_ID) if self._vm.selected_record else None

                for rec in items:
                    rec_id = rec.get(SC.K_ID)
                    is_selected = rec_id is not None and rec_id == selected_id

                    # Action buttons for row
                    action_buttons = ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_size=16,
                                icon_color=ft.Colors.PRIMARY,
                                tooltip="Chỉnh sửa",
                                on_click=lambda _, r=rec: self._open_edit_dialog(r),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=16,
                                icon_color=ft.Colors.ERROR,
                                tooltip="Xóa",
                                on_click=lambda _, r=rec: self._open_delete_dialog(r),
                            ),
                        ],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )

                    cell_contents: Dict[str, ft.Control] = {
                        SC.K_STT: ft.Text(
                            str(rec.get(SC.K_STT, "")),
                            color=ft.Colors.ON_SURFACE
                        ),
                        "thao_tac": action_buttons,
                    }

                    for col in self._table_col_keys:
                        if col in (SC.K_STT, "thao_tac"):
                            continue
                        cell_contents[col] = ft.Text(
                            str(rec.get(col, "") or ""),
                            color=ft.Colors.ON_SURFACE,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        )

                    row_cells = [
                        self._make_table_cell(cell_contents[k], k) for k in self._table_col_keys
                    ]

                    row_container = ft.Container(
                        content=ft.Row(
                            controls=row_cells,
                            spacing=self._col_spacing,
                        ),
                        width=self._total_row_width(),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=3),
                        border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                        bgcolor=ft.Colors.PRIMARY_CONTAINER if is_selected else None,
                        ink=True,
                        on_click=lambda _, r=rec: self._vm.set_selected_record(r),
                    )
                    rows.append(row_container)

                self._table_body_view.controls = rows
                self._empty_state.visible = total_items == 0
                self._table_body_view.visible = total_items > 0

                # Pagination display
                self._pagination_text.value = f"Trang {self._vm.current_page} / {self._vm.total_pages} (Tổng: {total_items})"
                self._btn_prev_page.disabled = self._vm.current_page <= 1
                self._btn_next_page.disabled = self._vm.current_page >= self._vm.total_pages

                self.page.update()
            except Exception as e:
                LoggerUtil.get_logger().error(f"MegawanMetronetPage _on_data_changed error: {e}")

        try:
            self.page.run_task(_apply)
        except Exception:
            pass

    def _on_selected_record_changed(self):
        async def _apply():
            try:
                rec = self._vm.selected_record
                if rec:
                    stt = rec.get(SC.K_STT, "N/A")
                    self._detail_title.value = f"Chi Tiết Bản Ghi: {stt}" if stt else f"Chi Tiết Bản Ghi"
                    self._btn_detail_edit.visible = True
                    self._btn_detail_delete.visible = True

                    for k, text_ctrl in self._detail_value_texts.items():
                        v = str(rec.get(k, "") or "")
                        text_ctrl.value = v if v.strip() else "—"
                else:
                    self._detail_title.value = "Chi Tiết Bản Ghi"
                    self._btn_detail_edit.visible = False
                    self._btn_detail_delete.visible = False
                    for text_ctrl in self._detail_value_texts.values():
                        text_ctrl.value = "—"

                # Update row highlights in table
                selected_id = rec.get(SC.K_ID) if rec else None
                paginated = self._vm.paginated_records
                for idx, row_container in enumerate(self._table_body_view.controls):
                    if idx < len(paginated):
                        row_rec = paginated[idx]
                        is_sel = selected_id is not None and row_rec.get(SC.K_ID) == selected_id
                        row_container.bgcolor = ft.Colors.PRIMARY_CONTAINER if is_sel else None

                self.page.update()
            except Exception as e:
                LoggerUtil.get_logger().error(f"MegawanMetronetPage _on_selected_record_changed error: {e}")

        try:
            self.page.run_task(_apply)
        except Exception:
            pass
