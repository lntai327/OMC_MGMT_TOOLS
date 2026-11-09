import truststore
truststore.inject_into_ssl()

import traceback
import flet as ft

from share.util.logger_util import LoggerUtil
from share.util.explorer_util import ExplorerUtil
from frontend.app import app_main


if __name__ == "__main__":
    # try:
    #     ExplorerUtil().updater()
    # except Exception:
    #     LoggerUtil.get_logger().warning("main: updater failed (non-fatal)")

    try:
        ExplorerUtil().clean_cache()
    except Exception:
        LoggerUtil.get_logger().warning("main: clean_cache failed (non-fatal)")

    try:
        ft.run(app_main)
    except Exception:
        tb = traceback.format_exc()
        LoggerUtil.get_logger().error(f"main: fatal error\n{tb}")