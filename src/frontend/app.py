import asyncio
import flet as ft

from backend.db.database import Database

from frontend.config.cfg import CFG
from share.constant import constant as SC
from frontend.routing.router import Router
from frontend.pages.db_config_page import DbConfigPage
from frontend.pages.login_page import LoginPage
from frontend.pages.home_page import HomePage
from frontend.pages.bc_cell_mll_page import BcCellMllPage

from share.session import Session
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil

ROUTES = {
    "db_config": DbConfigPage,
    # "login": LoginPage,
    # "home": HomePage,
    "bc_cell_mll": BcCellMllPage,
}

async def app_main(page: ft.Page):
    """Flet main function — configures the page and starts navigation."""
    # --- Window settings ---
    page.window.icon = str(
        ExplorerUtil().get_config_file_path("rpt_icon.ico")
    )
    page.title = (
        f"{CFG.get("app_name", 'OMC Report Tool')}"
        f" {CFG.get(SC.K_APP_VERSION, 'X')}"
        # f"{Session.get_role()}"
    )
    page.window.width = 900
    page.window.height = 800
    page.window.min_width = 900
    page.window.min_height = 800
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        # color_scheme=ft.ColorScheme(
        #     surface="#162233",
        #     on_surface="#E8F0FE",
        # ),
        # color_scheme_seed=ft.Colors.INDIGO,
        use_material3=True,
    )
    page.fonts = {
        "Roboto": "https://fonts.gstatic.com/s/roboto/v32/KFOmCnqEu92Fr1Mu4mxK.woff2",
    }
    page.padding = 0

    db_initialized = False
    try:
        await asyncio.to_thread(Database().init_db)
        db_initialized = True
    except Exception as exc:
        LoggerUtil.get_logger().error(f"main init_db failed: {exc}")

    # --- Router setup ---
    router = Router(page)
    router.register_routes(ROUTES)

    async def on_view_pop(view: ft.View):
        router.go_back()

    page.on_view_pop = on_view_pop

    # --- Start at DB config / connection check ---
    router.go("db_config")

    LoggerUtil.get_logger().info("app_main: started")
