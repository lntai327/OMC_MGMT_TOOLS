"""HomeViewModel — report list filter logic."""
from frontend.viewmodels.base_vm import BaseViewModel
import frontend.constant.type as FET


class HomeViewModel(BaseViewModel):
    """ViewModel for the Home (report selection) page.

    Observable keys:
        "filtered_reports" — list of report names matching search query
    """

    # All available reports
    ALL_REPORTS: list[str] = [
        FET.ReportTypeInfo.BC_CELL_MLL.report_name,
        FET.ReportTypeInfo.BC_BTS.report_name,
        FET.ReportTypeInfo.QLY_HSUAT_XGSPON.report_name,
    ]

    # Map report_name → route key
    REPORT_ROUTES: dict[str, str] = {
        FET.ReportTypeInfo.BC_CELL_MLL.report_name: "bc_cell_mll",
        FET.ReportTypeInfo.BC_BTS.report_name: "bc_bts",
        FET.ReportTypeInfo.QLY_HSUAT_XGSPON.report_name: "qly_hsuat_xgspon",
    }

    def __init__(self):
        super().__init__()
        self._search_query: str = ""
        self._filtered_reports: list[str] = list(self.ALL_REPORTS)

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def search_query(self) -> str:
        return self._search_query

    @property
    def filtered_reports(self) -> list[str]:
        return self._filtered_reports

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def update_filter(self, query: str) -> None:
        """Filter report list by query string (case-insensitive substring match)."""
        self._search_query = query
        q = query.strip().lower()
        self._filtered_reports = [r for r in self.ALL_REPORTS if q in r.lower()]
        self.notify("filtered_reports")

    def get_route_for_report(self, report_name: str) -> str | None:
        """Return the route key for a report name, or None if not found."""
        return self.REPORT_ROUTES.get(report_name)
