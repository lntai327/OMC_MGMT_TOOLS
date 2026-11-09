import flet as ft
from share.constant import constant as SC


class LoadingOverlay(ft.Stack):
    """Modern semi-transparent overlay with a spinner centered on screen.

    Usage:
        overlay = LoadingOverlay(on_cancel=vm.cancel)
        page_content = ft.Stack([main_content, overlay])
        overlay.visible = vm.is_loading
    """

    def __init__(self, message: str = "", on_cancel=None):
        self._on_cancel = on_cancel
        self._message = message or SC.K_UI_LOADING_TEXT

        # --- Animated spinner ---
        self._spinner = ft.ProgressRing(
            width=52,
            height=52,
            stroke_width=5,
            color=ft.Colors.PURPLE_200,
        )

        # --- Dot pulse row (decorative secondary indicator) ---
        dot_style = lambda delay: ft.Container(
            width=8,
            height=8,
            border_radius=4,
            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.PURPLE_200),
            animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
        )
        self._dots = ft.Row(
            [dot_style(0), dot_style(200), dot_style(400)],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        )

        # --- Message label ---
        self._label = ft.Text(
            self._message,
            size=15,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.PURPLE_600,
            text_align=ft.TextAlign.CENTER,
        )

        # --- Optional cancel button ---
        cancel_controls = []
        if on_cancel:
            cancel_controls.append(
                ft.Container(height=4),
            )
            cancel_controls.append(
                ft.OutlinedButton(
                    content=ft.Text(SC.K_UI_CANCEL), #, color=ft.Colors.WHITE70
                    style=ft.ButtonStyle(
                        side=ft.BorderSide(1, ft.Colors.WHITE38),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: self._on_cancel(),
                )
            )

        # --- Frosted-glass card ---
        card = ft.Container(
            content=ft.Column(
                [
                    self._spinner,
                    ft.Container(height=6),
                    self._dots,
                    ft.Container(height=10),
                    self._label,
                ]
                + cancel_controls,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                tight=True,
            ),
            width=220,
            padding=ft.Padding.only(left=32, top=36, right=32, bottom=32),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
            border=ft.Border(
                left=ft.BorderSide(1, ft.Colors.with_opacity(0.25, ft.Colors.WHITE)),
                top=ft.BorderSide(1, ft.Colors.with_opacity(0.25, ft.Colors.WHITE)),
                right=ft.BorderSide(1, ft.Colors.with_opacity(0.10, ft.Colors.WHITE)),
                bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.10, ft.Colors.WHITE)),
            ),
            # shadow=ft.BoxShadow(
            #     spread_radius=0,
            #     blur_radius=40,
            #     color=ft.Colors.with_opacity(0.45, ft.Colors.BLACK),
            #     offset=ft.Offset(0, 12),
            # ),
        )

        # --- Full-screen backdrop (covers entire Stack area) ---
        backdrop = ft.Container(
            content=card,
            alignment=ft.Alignment.CENTER,
            # bgcolor=ft.Colors.with_opacity(0.28, ft.Colors.BLACK),
            on_click=lambda _: None,
            expand=True,
        )

        super().__init__(
            controls=[backdrop],
            expand=True,
            visible=False,
        )

    def show(self, message: str = ""):
        if message:
            self._label.value = message
        self.visible = True

    def hide(self):
        self.visible = False
