import flet as ft

from frontend.component.update_db_dialog import UpdateDbDialog
from frontend.pages.base_page import BasePage
from frontend.viewmodels.qly_hsuat_gpon_vm import QlyHsuatGponViewModel
from frontend.component.explorer_ui_util import ExplorerUiUtil
from frontend.component.loading_overlay import LoadingOverlay
from frontend.component.common_view import safe_callback
import frontend.constant.type as FET
from share.session import Session
from share.constant import constant as SC
from share.constant import type as ST
from share.util.convert import to_float, to_int, to_site_ui
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.logger_util import LoggerUtil

class QlyHsuatGponPage(BasePage):
    title = FET.ReportTypeInfo.QLY_HSUAT_XGSPON.report_name
    scroll = None

    def __init__(self, page: ft.Page, router, **kwargs):
        super().__init__(page, router)
        self._update_db_dialog: UpdateDbDialog | None = None

        self._vm = QlyHsuatGponViewModel()
        self._vm.subscribe("is_loading", self._on_loading)
        self._vm.subscribe("data_changed", self._refresh_tghop_view)
        self._vm.subscribe("status_changed", self._on_status_changed)

        self._explorer_util = ExplorerUiUtil()
        self._explorer_util.register(page)

        self._is_admin = Session.is_admin()
        self._current_edit_ten_hthong = None
        self._delete_target_ten_hthong = None
        self._file_picker = ft.FilePicker()

        self._min_col_width: float = 40  # minimum column width when resizing
        self._col_spacing: float = 5    # spacing between columns (mirrors Row.spacing)
        self._has_previewed = False
        self._tghop_header_cells: dict[str, ft.Container] = {}
        self._detail_header_cells: dict[str, ft.Container] = {}

        self._slg_tbao_sfp = to_int(
            DynamicInfoUtil().get_value(
                2, SC.K_SCREEN_INPUT, "slg_tbao_fsp"
            ) or "40", True
        )

        # Default fixed widths for tong hop table (px)
        self._tghop_col_widths: dict[str, float] = {
            SC.K_STT: 50,
            SC.K_TEN_HE_THONG: 170,
            SC.K_IP: 90,
            SC.K_LOAI_OLT: 110,
            SC.K_MA_CSHT: 130,
            SC.K_TEN_CSHT: 110,
            SC.K_PHUONG_XA: 110,
            SC.K_TTVT: 220,
            SC.K_CARD_PON: 70,          # Số card thuê bao lắp đặt
            SC.K_CONG_PON: 70,          # Số cổng PON gắn SFP
            SC.K_SU_DUNG_1: 70,         # Số cổng PON sử dụng
            SC.K_ONT: 70,               # Số ONT sử dụng
            SC.K_SL_CARD_XGSPON: 75,    # Số lượng card XGSPON
            SC.K_VTRI_CARD_XGSPON: 70,  # Vị trí card XGSPON
            SC.K_TEN_CARD_XGSPON: 80,   # Tên card XGSPON
            SC.K_SL_SFP_XGSPON: 85,     # SL SFP XGSPON lắp đặt  (1)
            SC.K_SL_TB_XGSPON: 70,      # SL TB XGSPON (2)
            SC.K_HSUAT_1: 110,

            SC.K_GPON: 55, #Tghop GPON
            SC.K_MPM: 50, #Tghop MPM
            SC.K_N2: 50, #Tghop N2

            "thao_tac": 70,
        }

        # Default fixed widths for detail table (px)
        self._detail_col_widths: dict[str, float] = {
            SC.K_STT: 50,
            SC.K_TEN_HE_THONG: 170,
            SC.K_IP: 90,
            SC.K_LOAI_OLT: 110,
            SC.K_MA_CSHT: 130,
            SC.K_TEN_CSHT: 110,
            SC.K_TTVT: 220,
            SC.K_FRAME: 55,
            SC.K_SLOT: 40,
            SC.K_TEN_CARD: 65,
            SC.K_LOAI_CARD: 65,

            SC.K_SFP: 100, #Số cổng gắn SFP
            SC.K_CONG_PON: 110, #Số cổng PON sử dụng
            SC.K_ONT: 80, #Số ONT sử dụng

            SC.K_HSUAT_2: 80, # <= 30%
            SC.K_HSUAT_3: 90, # > 30% - <= 70%
            SC.K_HSUAT_4: 90, # > 70% - <= 90%
            SC.K_HSUAT_5: 80, # > 90%

            SC.K_GPON: 55, #Tghop GPON
            SC.K_MPM: 50, #Tghop MPM
            SC.K_N2: 50, #Tghop N2
        }

        # Column groups for multi-tier header
        self.GR_GPON_COLS = [
            SC.K_CARD_PON,
            SC.K_CONG_PON,
            SC.K_SU_DUNG_1,
            SC.K_ONT,
        ]

        self.GR_XGSPON_COLS = [
            SC.K_SL_CARD_XGSPON,
            SC.K_VTRI_CARD_XGSPON,
            SC.K_TEN_CARD_XGSPON,
            SC.K_SL_SFP_XGSPON,
            SC.K_SL_TB_XGSPON,
            SC.K_HSUAT_1,
        ]

        self.GR_HSUAT_COLS = [
            SC.K_HSUAT_2,
            SC.K_HSUAT_3,
            SC.K_HSUAT_4,
            SC.K_HSUAT_5,
        ]

        self.GR_TGHOP_SFP_COLS = [
            SC.K_GPON,
            SC.K_MPM,
            SC.K_N2,
        ]

    # ------------------------------------------------------------------
    # Build Page
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        if self._file_picker not in self.page.services:
            self.page.services.append(self._file_picker)

        col_header_style = ft.TextStyle(
            color=ft.Colors.ON_SURFACE_VARIANT,
            weight=ft.FontWeight.W_600,
        )

        self._header_hsuat_text = ft.Text(
            f"HS %\n(2) / ((1) * {self._slg_tbao_sfp})",
            style=col_header_style,
            text_align=ft.TextAlign.CENTER,
        )

        # Header label map (col_key -> label text / control)
        self._header_labels: dict[str, ft.Control | str] = {
            SC.K_STT: "STT",
            SC.K_TEN_HE_THONG: "Tên hệ thống",
            SC.K_IP: "IP",
            SC.K_LOAI_OLT: "Loại OLT",
            SC.K_MA_CSHT: "Mã CSHT",
            SC.K_TEN_CSHT: "Tên CSHT",
            SC.K_PHUONG_XA: "Phường/xã",
            SC.K_TTVT: "TTVT",
            SC.K_CARD_PON: "Số card TB lắp đặt",
            SC.K_CONG_PON: "Số cổng PON gắn SFP",
            SC.K_SU_DUNG_1: "Số cổng PON sử dụng",
            SC.K_ONT: "Số ONT sử dụng",
            SC.K_SL_CARD_XGSPON: "Số lượng card XGSPON",
            SC.K_VTRI_CARD_XGSPON: "Vị trí card XGSPON",
            SC.K_TEN_CARD_XGSPON: "Tên card XGSPON",
            SC.K_SL_SFP_XGSPON: "SL SFP XGSPON lắp đặt  (1)",
            SC.K_SL_TB_XGSPON: "SL TB XGSPON (2)",
            SC.K_HSUAT_1: self._header_hsuat_text, # custom control
            "thao_tac": "Thao tác",

            SC.K_FRAME: "Frame",
            SC.K_SLOT: "Slot",
            SC.K_TEN_CARD: "Tên card",
            SC.K_LOAI_CARD: "Loại card",

            SC.K_SFP: "Số cổng PON gắn SFP",
            SC.K_CONG_PON: "Số cổng PON sử dụng",
            SC.K_ONT: "Số ONT sử dụng",
            SC.K_HSUAT_2: "<=30%",
            SC.K_HSUAT_3: ">30%-70%",
            SC.K_HSUAT_4: ">70%-90%",
            SC.K_HSUAT_5: ">90%",
            SC.K_GPON: "GPON",
            SC.K_MPM: "MPM",
            SC.K_N2: "N2",
        }

        ##################### --- Loading overlay ---
        self._overlay = LoadingOverlay()

        ##################### --- Settings Dialog ---
        config_control_height = 100
        config_control_width = 200
        config_content_padding = ft.Padding(left=12, top=0, right=12, bottom=0)

        # site option
        self._site_dropdown = ft.Dropdown(
            label="Site",
            dense=True,
            border=ft.InputBorder.NONE,
            content_padding=config_content_padding,
            options=[
                ft.dropdown.Option("Đông"),
                ft.dropdown.Option("Tây"),
                ft.dropdown.Option("Tất Cả Site"),
            ],
            value=to_site_ui(self._vm.site),
            on_select=lambda e: self._on_site_dropdown(e.control.value),
        )

        # X th_bao/sfp
        self._tbao_sfp_dropdown = ft.Dropdown(
            label="S.lg T.Bao / SFP",
            dense=True,
            border=ft.InputBorder.NONE,
            content_padding=config_content_padding,
            options=[
                ft.dropdown.Option("40"),
                ft.dropdown.Option("50"),
                ft.dropdown.Option("64"),
            ],
            value=self._vm.slg_tbao_fsp,
            on_select=lambda e: self._on_tbao_sfp_dropdown(e.control.value),
        )

        # G.tri hsuat sfp c.báo
        self._gtri_hs_sfp_cbao_field = ft.TextField(
            label="G.tri H.Suất Khuyến nghị (%)",
            value=self._vm.gtri_hs_cbao,
            dense=True,
            border=ft.InputBorder.NONE,
            content_padding=config_content_padding,
            on_blur=lambda e: setattr(self._vm, "gtri_hs_cbao", e.control.value),
        )

        settings_controls = [
            self._make_tile(
                self._site_dropdown,
                width=config_control_width,
                height=config_control_height,
                expand=None,
            ),
            self._make_tile(
                self._tbao_sfp_dropdown,
                width=config_control_width,
                height=config_control_height,
                expand=None,
            ),
            self._make_tile(
                self._gtri_hs_sfp_cbao_field,
                width=config_control_width,
                height=config_control_height,
                expand=None,
            ),
        ]

        if self._is_admin:
            update_db_btn = ft.OutlinedButton(
                content=ft.Text(SC.K_UI_UPDATE_DB),
                icon=ft.Icons.UPLOAD_FILE,
                height=config_control_height,
                width=config_control_width,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=6),
                    padding=ft.Padding(left=18, top=0, right=18, bottom=0),
                ),
                on_click=lambda _: self._open_update_db(),
            )
            settings_controls.append(update_db_btn)

        self._settings_dialog = ft.AlertDialog(
            modal=False,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SETTINGS_OUTLINED, color=ft.Colors.PRIMARY, size=24),
                    ft.Text("Cài Đặt", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.W_600),
                ],
                spacing=10,
            ),
            bgcolor=ft.Colors.SURFACE,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=settings_controls,
                            spacing=16,
                            run_spacing=12,
                            wrap=True,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    tight=True,
                ),
                width=440,
                padding=10,
            ),
            actions=[
                ft.TextButton(
                    "Đóng",
                    on_click=lambda _: self._close_settings_dialog(),
                    style=ft.ButtonStyle(color=ft.Colors.PRIMARY),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        ##################### --- Filter Controls ---
        filter_control_height = 50
        filter_dropdown_width = 165
        filter_content_padding = ft.Padding(left=12, top=0, right=12, bottom=0)
        self._filter_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(key=SC.K_TEN_HE_THONG, text="Tên hệ thống"),
                ft.dropdown.Option(key=SC.K_IP, text="IP"),
                ft.dropdown.Option(key=SC.K_TTVT, text="TTVT"),
                ft.dropdown.Option(key=SC.K_PHUONG_XA, text="Phường/xã"),
            ],
            value=SC.K_TEN_HE_THONG,
            dense=True,
            border=ft.InputBorder.NONE,
            content_padding=ft.Padding(left=12, top=0, right=12, bottom=0),
            color=ft.Colors.ON_SURFACE,
            on_select=lambda e: self._apply_filter(),
        )

        self._search_input = ft.TextField(
            hint_text="Nhập từ khóa tìm kiếm...",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            border=ft.InputBorder.NONE,
            content_padding=ft.Padding(left=0, top=10, right=0, bottom=0),
            color=ft.Colors.ON_SURFACE,
            hint_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT),
            on_change=lambda e: self._apply_filter(),
            expand=True,
        )

        ##################### --- Pagination Controls ---
        self._page_size_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("10"),
                ft.dropdown.Option("20"),
                ft.dropdown.Option("50"),
                ft.dropdown.Option("100"),
            ],
            value=str(self._vm.page_size),
            width=100,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            color=ft.Colors.ON_SURFACE,
            border_color=ft.Colors.OUTLINE_VARIANT,
            focused_border_color=ft.Colors.PRIMARY,
            border_radius=8,
            on_select=lambda e: self._vm.set_page_size(int(e.control.value)),
        )

        self._pagination_text = ft.Text(
            "Trang 1 / 1 (Tổng: 0)", size=12, color=ft.Colors.ON_SURFACE_VARIANT
        )
        self._btn_prev_page = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_color=ft.Colors.ON_SURFACE_VARIANT,
            on_click=lambda _: self._vm.go_to_page(self._vm.current_page - 1),
        )
        self._btn_next_page = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_color=ft.Colors.ON_SURFACE_VARIANT,
            on_click=lambda _: self._vm.go_to_page(self._vm.current_page + 1),
        )

        ##################### --- Table "Tong hop" View Header & Container ---
        # TgHop Column keys in display order
        self._tghop_table_col_keys = [
            SC.K_STT, SC.K_TEN_HE_THONG, SC.K_IP, SC.K_LOAI_OLT,
            SC.K_MA_CSHT, SC.K_TEN_CSHT, SC.K_PHUONG_XA, SC.K_TTVT,
            SC.K_CARD_PON, SC.K_CONG_PON, SC.K_SU_DUNG_1, SC.K_ONT,
            SC.K_SL_CARD_XGSPON, SC.K_VTRI_CARD_XGSPON, SC.K_TEN_CARD_XGSPON,
            SC.K_SL_SFP_XGSPON, SC.K_SL_TB_XGSPON,
            SC.K_HSUAT_1,

            SC.K_GPON, SC.K_MPM, SC.K_N2,
            
            "thao_tac",
        ]

        # --- Build header row with resizable dividers ---
        self._tghop_header_table_row = self._build_tghop_header_row(
            col_header_style
        )

        self._header_table_tghop_container = ft.Container(
            content=self._tghop_header_table_row,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=ft.Padding.symmetric(horizontal=16, vertical=4),
            border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            width=self._tghop_total_row_width(),
        )

        # --- Tổng họp Table Body Rows (Scrollable View) ---
        self._tong_hop_table_view = ft.ListView(controls=[], expand=True)

        # --- Empty State ---
        self._empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.TABLE_ROWS_OUTLINED, size=56, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text("Chưa có bản ghi", size=15, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(vertical=60),
            visible=False,
        )

        # --- Horizontal-scrollable wrapper (header + body scroll together) ---
        # The inner column has an explicit width so it can overflow the
        # parent Row and trigger horizontal scrolling.
        self._tghop_table_inner_column = ft.Container(
            content=ft.Column(
                controls=[
                    self._header_table_tghop_container,
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                self._tong_hop_table_view,
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
            width=self._tghop_total_row_width(),
        )

        tong_hop_table_column = ft.Row(
            controls=[self._tghop_table_inner_column],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        ##################### Detail Table Dialog
        # Detail Column keys in display order
        self._detail_table_col_keys = [
            SC.K_STT, SC.K_TEN_HE_THONG, SC.K_IP, SC.K_LOAI_OLT,
            SC.K_MA_CSHT, SC.K_TEN_CSHT, SC.K_TTVT,
            SC.K_FRAME, SC.K_SLOT, SC.K_TEN_CARD, SC.K_LOAI_CARD,

            SC.K_SFP, SC.K_CONG_PON, SC.K_ONT,

            SC.K_HSUAT_2, SC.K_HSUAT_3, SC.K_HSUAT_4, SC.K_HSUAT_5,

            SC.K_GPON, SC.K_MPM, SC.K_N2
        ]

        self._detail_dialog_title = ft.Text(
            "Chi Tiết OLT",
            weight=ft.FontWeight.W_600,
            size=16,
            color=ft.Colors.ON_SURFACE,
        )

        self._detail_header_table_row = self._build_detail_header_row(col_header_style)

        self._header_table_detail_container = ft.Container(
            content=self._detail_header_table_row,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=ft.Padding.symmetric(horizontal=16, vertical=4),
            border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            width=self._total_detail_row_width(),
        )

        self._detail_table_view = ft.ListView(controls=[], expand=True)

        self._detail_empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.TABLE_ROWS_OUTLINED, size=48, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text("Không có bản ghi chi tiết", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(vertical=40),
            visible=False,
        )

        self._detail_table_inner_column = ft.Container(
            content=ft.Column(
                controls=[
                    self._header_table_detail_container,
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                self._detail_table_view,
                                self._detail_empty_state,
                            ],
                            expand=True,
                        ),
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            width=self._total_detail_row_width(),
        )

        self._detail_table_scroll_row = ft.Row(
            controls=[self._detail_table_inner_column],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        self._detail_dialog = ft.AlertDialog(
            modal=False,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.PRIMARY, size=24),
                    self._detail_dialog_title,
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.SURFACE,
            content=ft.Container(
                content=self._detail_table_scroll_row,
                width=1500,
                height=300,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            ),
            actions=[
                ft.TextButton(
                    "Đóng",
                    on_click=lambda _: self._close_detail_dialog(),
                    style=ft.ButtonStyle(color=ft.Colors.PRIMARY),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        ##################### --- Header Bar ---
        header_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.OutlinedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=18, color=ft.Colors.PRIMARY),
                                ft.Text("Cài đặt", color=ft.Colors.PRIMARY, size=13),
                            ],
                            spacing=6,
                            tight=True,
                        ),
                        on_click=lambda _: self._open_settings_dialog(),
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, ft.Colors.PRIMARY),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        height=38,
                        width= 150,
                    ),
                    ft.Container(width=8),
                    ft.OutlinedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.REMOVE_RED_EYE_OUTLINED, size=18, color=ft.Colors.PRIMARY),
                                ft.Text("Xem trước", color=ft.Colors.PRIMARY, size=13),
                            ],
                            spacing=6,
                            tight=True,
                        ),
                        on_click=lambda _: self._on_preview_click(),
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, ft.Colors.PRIMARY),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        height=38,
                        width= 150,
                    ),
                    ft.Container(width=8),
                    ft.OutlinedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.FILE_DOWNLOAD_OUTLINED, size=18, color=ft.Colors.PRIMARY),
                                ft.Text("Xuất Excel", color=ft.Colors.PRIMARY, size=13),
                            ],
                            spacing=6,
                            tight=True,
                        ),
                        on_click=lambda _: self._on_export_click(),
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, ft.Colors.PRIMARY),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        height=38,
                        width= 150,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

        ##################### --- Filter Bar ---
        filter_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "Bộ lọc:",
                            color=ft.Colors.ON_SURFACE,
                            weight=ft.FontWeight.W_500,
                        ),
                        alignment=ft.Alignment.CENTER,
                        height=filter_control_height,
                    ),
                    self._make_tile(
                        self._filter_dropdown,
                        width=165,
                        height=filter_control_height,
                    ),
                    self._make_tile(
                        self._search_input,
                        expand=True,
                        height=filter_control_height,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(
                horizontal=24,
                vertical=8,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border=ft.Border.only(
                bottom=ft.BorderSide(
                    1,
                    ft.Colors.OUTLINE_VARIANT,
                )
            ),
        )

        ##################### --- Pagination Bar ---
        pagination_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Hiển thị:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                            self._page_size_dropdown,
                        ],
                        spacing=6,
                    ),
                    ft.Container(expand=True),
                    self._pagination_text,
                    self._btn_prev_page,
                    self._btn_next_page,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=8),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border=ft.Border.only(top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

        #####################
        tong_hop_table_area = ft.Container(
            content=ft.Column(
                controls=[
                    tong_hop_table_column,
                ],
                expand=True,
                spacing=0,
            ),
            expand=True,
        )

        #####################
        main_layout = ft.Column(
            controls=[
                header_bar,
                filter_bar,
                tong_hop_table_area,
                pagination_bar,
            ],
            spacing=0,
            expand=True,
        )
        self._interactive_root = main_layout

        # self._on_preview_click()

        self.page.overlay.extend([self._settings_dialog, self._detail_dialog])

        return ft.Stack(
            controls=[
                main_layout,
                self._overlay,
            ],
            expand=True,
        )

    # ------------------------------------------------------------------
    # Table helpers – fixed-width cells & resizable header
    # ------------------------------------------------------------------

    def _tghop_total_row_width(self) -> float:
        """Calculate total row width from current column widths + spacing + padding."""
        n = len(self._tghop_table_col_keys)
        return sum(self._tghop_col_widths[k] for k in self._tghop_table_col_keys) + self._col_spacing * (n - 1) + 32  # 32 = horiz padding

    def _make_tghop_cell(self, content, col_key):
        """Create a fixed-width cell for a data row."""
        width = self._tghop_col_widths.get(col_key, self._min_col_width)
        align = ft.Alignment.CENTER if col_key in (SC.K_STT, SC.K_MA_TINH, SC.K_HSUAT_1, "thao_tac") \
            else ft.Alignment.CENTER_LEFT
        return ft.Container(
            content=content,
            width=width,
            alignment=align,
            border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.symmetric(horizontal=4),
        )

    def _make_detail_cell(self, content, col_key):
        """Create a fixed-width cell for a detail data row."""
        width = self._detail_col_widths.get(col_key, self._min_col_width)
        align = ft.Alignment.CENTER if col_key in (SC.K_STT, SC.K_FRAME, SC.K_SLOT) \
            else ft.Alignment.CENTER_LEFT
        return ft.Container(
            content=content,
            width=width,
            alignment=align,
            border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.symmetric(horizontal=4),
        )

    def _get_tghop_group_width(self, col_keys: list[str]) -> float:
        """Calculate total width for a column group including internal column spacing."""
        return sum(self._tghop_col_widths[k] for k in col_keys) + self._col_spacing * (len(col_keys) - 1)

    def _get_label_control(
        self, col_key: str, col_header_style: ft.TextStyle
    ) -> ft.Control:
        """Get or wrap a header label into a centered Text control."""
        label_or_ctrl = self._header_labels[col_key]
        if isinstance(label_or_ctrl, str):
            return ft.Text(
                label_or_ctrl,
                style=col_header_style,
                text_align=ft.TextAlign.CENTER,
            )
        return label_or_ctrl

    def _make_resizable_tghop_header_cell(
        self, label_ctrl: ft.Control, col_key: str, height: float = 95
    ) -> ft.Container:
        """Wrap a header label in a container with a draggable right-edge divider."""
        width = self._tghop_col_widths[col_key]
        align = ft.Alignment.CENTER

        divider = ft.GestureDetector(
            content=ft.Container(
                width=8,
                height=height,
                ink=True,
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_COLUMN,
            drag_interval=10,
            on_horizontal_drag_update=lambda e, _k=col_key: self._on_tghop_col_resize(e, _k),
        )

        cell = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=label_ctrl,
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

    def _build_tghop_header_row(
        self, col_header_style: ft.TextStyle
    ) -> ft.Row:
        """Build the multi-tier header row with draggable column-dividers for resizing."""
        self._tghop_header_cells.clear()

        top_group_height = 25
        sub_header_height = 60
        total_header_height = top_group_height + sub_header_height

        # Group 1: Thống kê mạng GPON
        gpon_w = self._get_tghop_group_width(self.GR_GPON_COLS)
        self._top_group_gpon_cell = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Thống kê mạng GPON",
                        style=col_header_style,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=gpon_w,
            height=top_group_height,
            border=ft.Border(
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
        )

        gpon_sub_cells = []
        for col_key in self.GR_GPON_COLS:
            cell = self._make_resizable_tghop_header_cell(
                self._get_label_control(col_key, col_header_style),
                col_key,
                height=sub_header_height,
            )
            self._tghop_header_cells[col_key] = cell
            gpon_sub_cells.append(cell)

        self._gpon_sub_row = ft.Row(
            controls=gpon_sub_cells,
            spacing=self._col_spacing,
        )
        self._group_gpon_container = ft.Container(
            content=ft.Column(
                controls=[
                    self._top_group_gpon_cell,
                    self._gpon_sub_row,
                ],
                spacing=0,
            ),
            width=gpon_w,
            height=total_header_height,
        )

        # Group 2: Thuê bao XGSPON
        xgspon_w = self._get_tghop_group_width(self.GR_XGSPON_COLS)
        self._top_group_xgspon_cell = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Thuê bao XGSPON",
                        style=col_header_style,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=xgspon_w,
            height=top_group_height,
            border=ft.Border(
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
        )

        xgspon_sub_cells = []
        for col_key in self.GR_XGSPON_COLS:
            cell = self._make_resizable_tghop_header_cell(
                self._get_label_control(col_key, col_header_style),
                col_key,
                height=sub_header_height,
            )
            self._tghop_header_cells[col_key] = cell
            xgspon_sub_cells.append(cell)

        self._xgspon_sub_row = ft.Row(
            controls=xgspon_sub_cells,
            spacing=self._col_spacing,
        )
        self._group_xgspon_container = ft.Container(
            content=ft.Column(
                controls=[
                    self._top_group_xgspon_cell,
                    self._xgspon_sub_row,
                ],
                spacing=0,
            ),
            width=xgspon_w,
            height=total_header_height,
        )

        # Group 3: Tổng hợp SFP
        tghop_sfp_w = self._get_tghop_group_width(self.GR_TGHOP_SFP_COLS)
        self._top_group_tghop_sfp_cell = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Tổng hợp SFP",
                        style=col_header_style,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=tghop_sfp_w,
            height=top_group_height,
            border=ft.Border(
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
        )

        tghop_sfp_sub_cells = []
        for col_key in self.GR_TGHOP_SFP_COLS:
            cell = self._make_resizable_tghop_header_cell(
                self._get_label_control(col_key, col_header_style),
                col_key,
                height=sub_header_height,
            )
            self._tghop_header_cells[col_key] = cell
            tghop_sfp_sub_cells.append(cell)

        self._tghop_sfp_sub_row = ft.Row(
            controls=tghop_sfp_sub_cells,
            spacing=self._col_spacing,
        )
        self._group_tghop_sfp_container = ft.Container(
            content=ft.Column(
                controls=[
                    self._top_group_tghop_sfp_cell,
                    self._tghop_sfp_sub_row,
                ],
                spacing=0,
            ),
            width=tghop_sfp_w,
            height=total_header_height,
        )

        # Assemble outer row
        outer_cells = []
        for col_key in self._tghop_table_col_keys:
            if col_key in self.GR_GPON_COLS:
                if col_key == self.GR_GPON_COLS[0]:
                    outer_cells.append(self._group_gpon_container)
                continue

            if col_key in self.GR_XGSPON_COLS:
                if col_key == self.GR_XGSPON_COLS[0]:
                    outer_cells.append(self._group_xgspon_container)
                continue

            if col_key in self.GR_TGHOP_SFP_COLS:
                if col_key == self.GR_TGHOP_SFP_COLS[0]:
                    outer_cells.append(self._group_tghop_sfp_container)
                continue

            label_ctrl = self._get_label_control(col_key, col_header_style)
            cell = self._make_resizable_tghop_header_cell(
                label_ctrl,
                col_key,
                height=total_header_height,
            )
            self._tghop_header_cells[col_key] = cell
            outer_cells.append(cell)

        return ft.Row(
            controls=outer_cells,
            spacing=self._col_spacing,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _total_detail_row_width(self) -> float:
        """Calculate total row width for detail table from detail column widths + spacing + padding."""
        n = len(self._detail_table_col_keys)
        return sum(self._detail_col_widths.get(k, 80) for k in self._detail_table_col_keys) + self._col_spacing * (n - 1) + 32

    def _get_detail_group_width(self, col_keys: list[str]) -> float:
        """Calculate total width for a detail column group including internal column spacing."""
        return sum(self._detail_col_widths[k] for k in col_keys) + self._col_spacing * (len(col_keys) - 1)

    def _make_detail_resizable_header_cell(
        self, label_ctrl: ft.Control, col_key: str, height: float = 45
    ) -> ft.Container:
        """Wrap a detail header label in a container with a draggable right-edge divider."""
        width = self._detail_col_widths.get(col_key, 80)
        align = ft.Alignment.CENTER

        divider = ft.GestureDetector(
            content=ft.Container(
                width=8,
                height=height,
                ink=True,
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_COLUMN,
            drag_interval=10,
            on_horizontal_drag_update=lambda e, _k=col_key: self._on_detail_col_resize(e, _k),
        )

        cell = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=label_ctrl,
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

    def _build_detail_header_row(
        self, col_header_style: ft.TextStyle
    ) -> ft.Row:
        """Build the multi-tier header row for detail table with draggable column-dividers."""
        self._detail_header_cells.clear()

        top_group_height = 25
        sub_header_height = 45
        total_header_height = top_group_height + sub_header_height

        # Group 1: Hiệu suất cổng PON
        hsuat_w = self._get_detail_group_width(self.GR_HSUAT_COLS)
        self._top_group_hsuat_cell = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Hiệu suất cổng PON",
                        style=col_header_style,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=hsuat_w,
            height=top_group_height,
            border=ft.Border(
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
        )

        hsuat_sub_cells = []
        for col_key in self.GR_HSUAT_COLS:
            label_text = self._header_labels.get(col_key, col_key)
            label_ctrl = ft.Text(
                label_text,
                style=col_header_style,
                text_align=ft.TextAlign.CENTER,
            )
            cell = self._make_detail_resizable_header_cell(
                label_ctrl,
                col_key,
                height=sub_header_height,
            )
            self._detail_header_cells[col_key] = cell
            hsuat_sub_cells.append(cell)

        self._hsuat_sub_row = ft.Row(
            controls=hsuat_sub_cells,
            spacing=self._col_spacing,
        )
        self._group_hsuat_container = ft.Container(
            content=ft.Column(
                controls=[
                    self._top_group_hsuat_cell,
                    self._hsuat_sub_row,
                ],
                spacing=0,
            ),
            width=hsuat_w,
            height=total_header_height,
        )

        # Group 2: Tổng hợp SFP
        sfp_w = self._get_detail_group_width(self.GR_TGHOP_SFP_COLS)
        self._top_group_detail_sfp_cell = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Tổng hợp SFP",
                        style=col_header_style,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=sfp_w,
            height=top_group_height,
            border=ft.Border(
                bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
        )

        sfp_sub_cells = []
        for col_key in self.GR_TGHOP_SFP_COLS:
            label_text = self._header_labels.get(col_key, col_key)
            label_ctrl = ft.Text(
                label_text,
                style=col_header_style,
                text_align=ft.TextAlign.CENTER,
            )
            cell = self._make_detail_resizable_header_cell(
                label_ctrl,
                col_key,
                height=sub_header_height,
            )
            self._detail_header_cells[col_key] = cell
            sfp_sub_cells.append(cell)

        self._detail_sfp_sub_row = ft.Row(
            controls=sfp_sub_cells,
            spacing=self._col_spacing,
        )
        self._group_detail_sfp_container = ft.Container(
            content=ft.Column(
                controls=[
                    self._top_group_detail_sfp_cell,
                    self._detail_sfp_sub_row,
                ],
                spacing=0,
            ),
            width=sfp_w,
            height=total_header_height,
        )

        # Assemble outer row
        outer_cells = []
        for col_key in self._detail_table_col_keys:
            if col_key in self.GR_HSUAT_COLS:
                if col_key == self.GR_HSUAT_COLS[0]:
                    outer_cells.append(self._group_hsuat_container)
                continue

            if col_key in self.GR_TGHOP_SFP_COLS:
                if col_key == self.GR_TGHOP_SFP_COLS[0]:
                    outer_cells.append(self._group_detail_sfp_container)
                continue

            label_text = self._header_labels.get(col_key, col_key)
            label_ctrl = ft.Text(
                label_text,
                style=col_header_style,
                text_align=ft.TextAlign.CENTER,
            )
            cell = self._make_detail_resizable_header_cell(
                label_ctrl,
                col_key,
                height=total_header_height,
            )
            self._detail_header_cells[col_key] = cell
            outer_cells.append(cell)

        return ft.Row(
            controls=outer_cells,
            spacing=self._col_spacing,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _on_detail_col_resize(self, e: ft.DragUpdateEvent, col_key: str):
        """Handle drag on a header divider in detail table to resize a column."""
        new_width = self._detail_col_widths.get(col_key, 80) + (e.primary_delta or 0)
        if new_width < self._min_col_width:
            new_width = self._min_col_width
        self._detail_col_widths[col_key] = new_width
        self._rebuild_detail_table_widths()

    def _rebuild_detail_table_widths(self):
        """Synchronise detail table visible cells / header to current _detail_col_widths."""
        if not hasattr(self, "_detail_header_cells") or not self._detail_header_cells:
            return

        total_w = self._total_detail_row_width()

        for col_key, cell_container in self._detail_header_cells.items():
            cell_container.width = self._detail_col_widths.get(col_key, self._min_col_width)

        # Update group containers
        hsuat_w = self._get_detail_group_width(self.GR_HSUAT_COLS)
        if hasattr(self, "_top_group_hsuat_cell") and self._top_group_hsuat_cell:
            self._top_group_hsuat_cell.width = hsuat_w
        if hasattr(self, "_group_hsuat_container") and self._group_hsuat_container:
            self._group_hsuat_container.width = hsuat_w

        sfp_w = self._get_detail_group_width(self.GR_TGHOP_SFP_COLS)
        if hasattr(self, "_top_group_detail_sfp_cell") and self._top_group_detail_sfp_cell:
            self._top_group_detail_sfp_cell.width = sfp_w
        if hasattr(self, "_group_detail_sfp_container") and self._group_detail_sfp_container:
            self._group_detail_sfp_container.width = sfp_w

        if hasattr(self, "_header_table_detail_container") and self._header_table_detail_container:
            self._header_table_detail_container.width = total_w
        if hasattr(self, "_detail_table_inner_column") and self._detail_table_inner_column:
            self._detail_table_inner_column.width = total_w

        if hasattr(self, "_detail_table_view") and self._detail_table_view:
            for row_container in self._detail_table_view.controls:
                if not isinstance(row_container, ft.Container):
                    continue
                row_ctrl = row_container.content
                if not isinstance(row_ctrl, ft.Row):
                    continue
                for body_cell, col_key in zip(row_ctrl.controls, self._detail_table_col_keys):
                    body_cell.width = self._detail_col_widths.get(col_key, self._min_col_width)
                row_container.width = total_w

        try:
            self.page.update()
        except Exception:
            pass

    def _on_tghop_col_resize(self, e: ft.DragUpdateEvent, col_key: str):
        """Handle drag on a header divider to resize a column."""
        new_width = self._tghop_col_widths[col_key] + (e.primary_delta or 0)
        if new_width < self._min_col_width:
            new_width = self._min_col_width
        self._tghop_col_widths[col_key] = new_width
        self._rebuild_tghop_table_widths()

    def _rebuild_tghop_table_widths(self):
        """Synchronise every visible cell / header to the current _col_widths."""
        total_w = self._tghop_total_row_width()

        # Update header cells
        for col_key, cell_container in self._tghop_header_cells.items():
            cell_container.width = self._tghop_col_widths[col_key]

        # Update group containers
        gpon_w = self._get_tghop_group_width(self.GR_GPON_COLS)
        if hasattr(self, "_top_group_gpon_cell") and self._top_group_gpon_cell:
            self._top_group_gpon_cell.width = gpon_w
        if hasattr(self, "_group_gpon_container") and self._group_gpon_container:
            self._group_gpon_container.width = gpon_w

        xgspon_w = self._get_tghop_group_width(self.GR_XGSPON_COLS)
        if hasattr(self, "_top_group_xgspon_cell") and self._top_group_xgspon_cell:
            self._top_group_xgspon_cell.width = xgspon_w
        if hasattr(self, "_group_xgspon_container") and self._group_xgspon_container:
            self._group_xgspon_container.width = xgspon_w

        tghop_sfp_w = self._get_tghop_group_width(self.GR_TGHOP_SFP_COLS)
        if hasattr(self, "_top_group_tghop_sfp_cell") and self._top_group_tghop_sfp_cell:
            self._top_group_tghop_sfp_cell.width = tghop_sfp_w
        if hasattr(self, "_group_tghop_sfp_container") and self._group_tghop_sfp_container:
            self._group_tghop_sfp_container.width = tghop_sfp_w

        if hasattr(self, "_header_table_tghop_container") and self._header_table_tghop_container:
            self._header_table_tghop_container.width = total_w
        if hasattr(self, "_tghop_table_inner_column") and self._tghop_table_inner_column:
            self._tghop_table_inner_column.width = total_w

        # Update body rows
        for row_container in self._tong_hop_table_view.controls:
            if not isinstance(row_container, ft.Container):
                continue
            row_ctrl = row_container.content  # ft.Row
            if not isinstance(row_ctrl, ft.Row):
                continue
            for body_cell, col_key in zip(row_ctrl.controls, self._tghop_table_col_keys):
                body_cell.width = self._tghop_col_widths[col_key]
            row_container.width = total_w

        try:
            self.page.update()
        except Exception:
            pass

    def _make_tile(
        self,
        content: ft.Control,
        width: int | None = None,
        height: int | None = None,
        expand: bool = False,
        padding: ft.Padding | None = None,
    ) -> ft.Container:
        return ft.Container(
            content=content,
            height=height,
            width=width,
            expand=expand,
            padding=padding,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=6,
            alignment=ft.Alignment.CENTER,
        )

    # ------------------------------------------------------------------
    # VM Subscribers & View Refresh
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
                LoggerUtil.get_logger().error(f"QlyHsuatGponPage _on_loading error: {e}")

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
                        path=self._vm.path_message
                    )
            except Exception as e:
                LoggerUtil.get_logger().error(f"QlyHsuatGponPage _on_status_changed error: {e}")

        try:
            self.page.run_task(_apply)
        except Exception:
            pass

    def _refresh_tghop_view(self):
        async def _apply():
            try:
                self._page_size_dropdown.value = str(self._vm.page_size)

                current_items: list[dict] = self._vm.paginated_record
                total_items = len(self._vm.filtered_record)

                # Render Table Rows
                rows = []

                def make_detail_handler(rec):
                    return lambda _: self._open_detail_dialog(rec)

                for record in current_items:
                    action_controls = [
                        ft.IconButton(
                            icon=ft.Icons.INFO_OUTLINE,
                            icon_color=ft.Colors.ON_SURFACE_VARIANT,
                            tooltip="Xem chi tiết",
                            icon_size=18,
                            on_click=make_detail_handler(record),
                        )
                    ]

                    ten_he_thong = record.get(SC.K_TEN_HE_THONG, "")
                    detail_records = self._vm.get_detail_records_by_ten_hthong(ten_he_thong)
                    total_gpon = sum(to_int(item.get(SC.K_GPON, 0)) for item in detail_records)
                    total_mpm = sum(to_int(item.get(SC.K_MPM, 0)) for item in detail_records)
                    total_n2 = sum(to_int(item.get(SC.K_N2, 0)) for item in detail_records)

                    # Build cell content map for this record
                    cell_contents: dict[str, ft.Control] = {
                        SC.K_STT: ft.Text(str(record.get(SC.K_STT, "")), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_TEN_HE_THONG: ft.Text(record.get(SC.K_TEN_HE_THONG, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_IP: ft.Text(record.get(SC.K_IP, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_LOAI_OLT: ft.Text(record.get(SC.K_LOAI_OLT, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_MA_CSHT: ft.Text(record.get(SC.K_MA_CSHT, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_TEN_CSHT: ft.Text(record.get(SC.K_TEN_CSHT, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_PHUONG_XA: ft.Text(record.get(SC.K_PHUONG_XA, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_TTVT: ft.Text(record.get(SC.K_TTVT, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_CARD_PON: ft.Text(record.get(SC.K_CARD_PON, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_CONG_PON: ft.Text(record.get(SC.K_CONG_PON, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_SU_DUNG_1: ft.Text(record.get(SC.K_SU_DUNG_1, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_ONT: ft.Text(record.get(SC.K_ONT, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_SL_CARD_XGSPON: ft.Text(record.get(SC.K_SL_CARD_XGSPON, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_VTRI_CARD_XGSPON: ft.Text(record.get(SC.K_VTRI_CARD_XGSPON, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_TEN_CARD_XGSPON: ft.Text(record.get(SC.K_TEN_CARD_XGSPON, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_SL_SFP_XGSPON: ft.Text(record.get(SC.K_SL_SFP_XGSPON, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_SL_TB_XGSPON: ft.Text(record.get(SC.K_SL_TB_XGSPON, ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_HSUAT_1: ft.Text(
                            round(to_float(record.get(SC.K_HSUAT_1, "")) * 100, 2),
                            color=ft.Colors.ON_SURFACE, size=13,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        SC.K_GPON: ft.Text(str(total_gpon), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_MPM: ft.Text(str(total_mpm), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        SC.K_N2: ft.Text(str(total_n2), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                        "thao_tac": ft.Row(
                            controls=action_controls, spacing=0,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    }

                    row_cells = [
                        self._make_tghop_cell(cell_contents[k], k) for k in self._tghop_table_col_keys
                    ]

                    rows.append(
                        ft.Container(
                            content=ft.Row(
                                controls=row_cells,
                                spacing=self._col_spacing,
                            ),
                            width=self._tghop_total_row_width(),
                            padding=ft.Padding.symmetric(horizontal=16, vertical=2),
                            border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                            on_click=make_detail_handler(record),
                        )
                    )
 
                self._tong_hop_table_view.controls = rows

                # Empty state & visibility
                self._empty_state.visible = (total_items == 0)
                self._tong_hop_table_view.visible = (total_items > 0)
 
                # Pagination controls state
                self._pagination_text.value = \
                    f"Trang {self._vm.current_page} / {self._vm.total_pages} (Tổng: {total_items})"
                self._btn_prev_page.disabled = (self._vm.current_page <= 1)
                self._btn_next_page.disabled = (self._vm.current_page >= self._vm.total_pages)
 
                self.page.update()
            except Exception:
                pass

        try:
            self.page.run_task(_apply)
        except Exception:
            pass
 
    # ------------------------------------------------------------------
    # Actions & Dialog Handlers
    # ------------------------------------------------------------------

    @safe_callback(lambda self: self.page)
    def _apply_filter(self):
        self._vm.set_filter(
            field=self._filter_dropdown.value or SC.K_TEN_HE_THONG,
            value=self._search_input.value or "",
        )

    @safe_callback(lambda self: self.page)
    def _open_settings_dialog(self):
        self._settings_dialog.open = True
        self.page.update()

    @safe_callback(lambda self: self.page)
    def _close_settings_dialog(self):
        self._settings_dialog.open = False
        self.page.update()

    @safe_callback(lambda self: self.page)
    def _open_detail_dialog(self, record: dict):
        ten_he_thong = record.get(SC.K_TEN_HE_THONG, "")
        records = self._vm.get_detail_records_by_ten_hthong(ten_he_thong)
        self._populate_detail_table(ten_he_thong, records)
        self._detail_dialog.open = True
        self.page.update()

    @safe_callback(lambda self: self.page)
    def _close_detail_dialog(self):
        self._detail_dialog.open = False
        self.page.update()

    def _populate_detail_table(self, ten_he_thong: str, records: list[dict]):
        self._detail_dialog_title.value = f"Chi Tiết OLT - {ten_he_thong}"

        if not records:
            self._detail_empty_state.visible = True
            self._detail_table_view.visible = False
            self._detail_table_view.controls = []
            return

        self._detail_empty_state.visible = False
        self._detail_table_view.visible = True

        rows = []
        for idx, item in enumerate(records, 1):
            cell_contents: dict[str, ft.Control] = {
                SC.K_STT: ft.Text(str(item.get(SC.K_STT) or idx), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_TEN_HE_THONG: ft.Text(str(item.get(SC.K_TEN_HE_THONG, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_IP: ft.Text(str(item.get(SC.K_IP, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_LOAI_OLT: ft.Text(str(item.get(SC.K_LOAI_OLT, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_MA_CSHT: ft.Text(str(item.get(SC.K_MA_CSHT, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_TEN_CSHT: ft.Text(str(item.get(SC.K_TEN_CSHT, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_TTVT: ft.Text(str(item.get(SC.K_TTVT) or item.get(SC.K_TTVT, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_FRAME: ft.Text(str(item.get(SC.K_FRAME, "") if item.get(SC.K_FRAME) is not None else ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_SLOT: ft.Text(str(item.get(SC.K_SLOT, "") if item.get(SC.K_SLOT) is not None else ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_TEN_CARD: ft.Text(str(item.get(SC.K_TEN_CARD, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_LOAI_CARD: ft.Text(str(item.get(SC.K_LOAI_CARD, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),

                SC.K_SFP: ft.Text(str(item.get(SC.K_SFP, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_CONG_PON: ft.Text(str(item.get(SC.K_CONG_PON, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_ONT: ft.Text(str(item.get(SC.K_ONT, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),

                SC.K_HSUAT_2: ft.Text(str(item.get(SC.K_HSUAT_2, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_HSUAT_3: ft.Text(str(item.get(SC.K_HSUAT_3, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_HSUAT_4: ft.Text(str(item.get(SC.K_HSUAT_4, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_HSUAT_5: ft.Text(str(item.get(SC.K_HSUAT_5, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),

                SC.K_GPON: ft.Text(str(item.get(SC.K_GPON, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_MPM: ft.Text(str(item.get(SC.K_MPM, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
                SC.K_N2: ft.Text(str(item.get(SC.K_N2, "") or ""), color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS),
            }

            row_cells = [
                self._make_detail_cell(cell_contents[k], k) for k in self._detail_table_col_keys
            ]

            rows.append(
                ft.Container(
                    content=ft.Row(
                        controls=row_cells,
                        spacing=self._col_spacing,
                    ),
                    width=self._total_detail_row_width(),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=4),
                    border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                )
            )

        self._detail_table_view.controls = rows

        total_w = self._total_detail_row_width()
        if hasattr(self, "_header_table_detail_container") and self._header_table_detail_container:
            self._header_table_detail_container.width = total_w
        if hasattr(self, "_detail_table_inner_column") and self._detail_table_inner_column:
            self._detail_table_inner_column.width = total_w

    @safe_callback(lambda self: self.page)
    def _on_export_click(self):
        async def _async_export():
            folder_path = await self._file_picker.get_directory_path(
                dialog_title="Chọn thư mục xuất dữ liệu Excel",
            )
            if folder_path:
                self.page.run_thread(lambda: self._vm.export_to_excel(folder_path))

        self.page.run_task(_async_export)

    @safe_callback(lambda self: self.page)
    def _open_update_db(self):
        if self._update_db_dialog is None:
            self._update_db_dialog = UpdateDbDialog(
                self.page,
                self._vm.get_db_update_list(),
                on_db_updated=self._on_refresh,
            )
        self._update_db_dialog.open()

    @safe_callback(lambda self: self.page)
    def _on_refresh(self):
        if self._has_previewed:
            self._vm.load_in_background(self.page)

    @safe_callback(lambda self: self.page)
    def _on_preview_click(self):
        self._has_previewed = True
        self._vm.load_in_background(self.page)

    @safe_callback(lambda self: self.page)
    def _on_tbao_sfp_dropdown(self, value):
        self._slg_tbao_sfp = to_int(value, True) or value
        if hasattr(self, "_header_hsuat_text") and self._header_hsuat_text:
            self._header_hsuat_text.value = f"HS %\n(2) / ((1) * {self._slg_tbao_sfp})"
        self.page.update()

        setattr(self._vm, "slg_tbao_fsp", value)
        #
        self._on_refresh()

    @safe_callback(lambda self: self.page)
    def _on_site_dropdown(self, value):
        match str(value).lower():
            case "đông":
                value = ST.Site.DONG.value
            case "tây":
                value = ST.Site.TAY.value
            case "tất cả site":
                value = ST.Site.ALL_SITE.value

        setattr(self._vm, "site", value)
        #
        self._on_refresh()