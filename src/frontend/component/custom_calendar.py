import calendar
import datetime
import flet as ft


class CalendarCustom(ft.Container):
    def __init__(self, on_date_selected=None):
        super().__init__()
        self.selected_date = datetime.date.today()
        self.current_display_date = datetime.date.today()
        self.on_date_selected = on_date_selected

        # Styling properties
        self.width = 420  # Slightly increased width to fit year navigation comfortable
        self.padding = 16
        self.border_radius = 16
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)

        # UI Control References
        self.month_year_text = ft.Text(
            weight=ft.FontWeight.BOLD,
            size=16,
            color=ft.Colors.ON_SURFACE,
        )
        self.grid_column = ft.Column(spacing=4)

        # Build initial layout structure
        self.content = ft.Column(
            controls=[
                self._build_header(),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                self._build_weekday_header(),
                self.grid_column,
            ],
            spacing=10,
            tight=True,
        )

    def did_mount(self):
        """Lifecycle hook called AFTER control is added to page"""
        self._render_calendar()

    def _build_header(self):
        """Header with Month/Year and Navigation Buttons (Year and Month)"""
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                self.month_year_text,
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT,
                            tooltip="Previous Year",
                            on_click=self._prev_year,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CHEVRON_LEFT,
                            tooltip="Previous Month",
                            on_click=self._prev_month,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CHEVRON_RIGHT,
                            tooltip="Next Month",
                            on_click=self._next_month,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT,
                            tooltip="Next Year",
                            on_click=self._next_year,
                        ),
                    ],
                    spacing=0,
                ),
            ],
        )

    def _build_weekday_header(self):
        """Header row showing 'Wk' (Week Number column) and Days of the Week"""
        days = ["Wk", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        day,
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=(
                            ft.Colors.PRIMARY
                            if idx == 0
                            else ft.Colors.ON_SURFACE_VARIANT
                        ),
                    ),
                    width=40,
                    height=30,
                    alignment=ft.Alignment.CENTER,
                )
                for idx, day in enumerate(days)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _render_calendar(self):
        """Renders the calendar matrix for the current year and month"""
        year = self.current_display_date.year
        month = self.current_display_date.month

        # Update Header Text
        self.month_year_text.value = self.current_display_date.strftime("%B %Y")

        # Clear existing grid
        self.grid_column.controls.clear()

        # Get weeks array (each week is a list of 7 datetime.date objects)
        cal = calendar.Calendar(firstweekday=0)  # 0 = Monday
        month_weeks = cal.monthdatescalendar(year, month)

        today = datetime.date.today()

        for week in month_weeks:
            row_controls = []

            # 1. Week Number Column (using ISO week number)
            iso_week_num = week[0].isocalendar().week
            week_num_cell = ft.Container(
                content=ft.Text(
                    f"W{iso_week_num:02d}",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PRIMARY,
                ),
                width=40,
                height=40,
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                border_radius=8,
            )
            row_controls.append(week_num_cell)

            # 2. Days of the Week Columns
            for day in week:
                is_current_month = day.month == month
                is_today = day == today
                is_selected = day == self.selected_date

                # Determine background and text colors
                if is_selected:
                    bg_color = ft.Colors.PRIMARY
                    text_color = ft.Colors.ON_PRIMARY
                elif is_today:
                    bg_color = ft.Colors.SECONDARY_CONTAINER
                    text_color = ft.Colors.ON_SECONDARY_CONTAINER
                else:
                    bg_color = ft.Colors.TRANSPARENT
                    text_color = (
                        ft.Colors.ON_SURFACE
                        if is_current_month
                        else ft.Colors.OUTLINE
                    )

                day_cell = ft.Container(
                    content=ft.Text(
                        str(day.day),
                        size=13,
                        weight=(
                            ft.FontWeight.BOLD
                            if (is_selected or is_today)
                            else ft.FontWeight.NORMAL
                        ),
                        color=text_color,
                    ),
                    width=40,
                    height=40,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=bg_color,
                    border_radius=20,  # Circular button
                    ink=True,
                    on_click=lambda e, d=day: self._select_date(d),
                )
                row_controls.append(day_cell)

            self.grid_column.controls.append(
                ft.Row(
                    controls=row_controls,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        # Only update if attached to a mounted page
        if self.page:
            self.update()

    def _prev_year(self, e):
        """Navigate to the same month in the previous year handling leap years safely"""
        year = self.current_display_date.year - 1
        month = self.current_display_date.month
        day = min(
            self.current_display_date.day, calendar.monthrange(year, month)[1]
        )
        self.current_display_date = datetime.date(year, month, day)
        self._render_calendar()

    def _next_year(self, e):
        """Navigate to the same month in the next year handling leap years safely"""
        year = self.current_display_date.year + 1
        month = self.current_display_date.month
        day = min(
            self.current_display_date.day, calendar.monthrange(year, month)[1]
        )
        self.current_display_date = datetime.date(year, month, day)
        self._render_calendar()

    def _prev_month(self, e):
        first_of_curr = self.current_display_date.replace(day=1)
        prev_month_date = first_of_curr - datetime.timedelta(days=1)
        self.current_display_date = prev_month_date
        self._render_calendar()

    def _next_month(self, e):
        days_in_month = calendar.monthrange(
            self.current_display_date.year, self.current_display_date.month
        )[1]
        last_of_curr = self.current_display_date.replace(day=days_in_month)
        next_month_date = last_of_curr + datetime.timedelta(days=1)
        self.current_display_date = next_month_date
        self._render_calendar()

    def _select_date(self, day: datetime.date):
        self.selected_date = day
        if day.month != self.current_display_date.month:
            self.current_display_date = day
        self._render_calendar()

        if self.on_date_selected:
            self.on_date_selected(day)


# --- Example Usage Application ---
def main(page: ft.Page):
    page.title = "Custom Week-Number Calendar"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK

    selected_text = ft.Text(
        f"Selected Date: {datetime.date.today().strftime('%Y-%m-%d')}",
        size=16,
        weight=ft.FontWeight.W_500,
    )

    def on_date_change(new_date: datetime.date):
        iso_year, iso_week, iso_day = new_date.isocalendar()
        selected_text.value = (
            f"Selected Date: {new_date.strftime('%Y-%m-%d')} (Week {iso_week})"
        )
        page.update()

    calendar_widget = CalendarCustom(on_date_selected=on_date_change)

    page.add(
        ft.Column(
            controls=[
                calendar_widget,
                ft.Container(height=10),
                selected_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


if __name__ == "__main__":
    ft.run(main)