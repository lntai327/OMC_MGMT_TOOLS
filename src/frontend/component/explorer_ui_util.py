import os
import subprocess
from typing import Callable, Optional

import flet as ft
from share.util.logger_util import LoggerUtil


class ExplorerUiUtil:
    """Wraps Flet's ft.FilePicker service for file selection and opens Windows Explorer for results.

    Usage:
        util = ExplorerUiUtil()
        util.register(page)  # call once after page is available
        util.pick_file(on_result=lambda path: vm.set_alarm_file(path))
    """

    def __init__(self):
        self._page: Optional[ft.Page] = None
        self._picker: Optional[ft.FilePicker] = None

    def register(self, page: ft.Page) -> None:
        """Register the Flet page instance.

        Must be called once before using pick_file().
        """
        self._page = page

    def pick_file(self, on_result: Callable[[Optional[str]], None],
                  allowed_extensions: list[str] | None = None) -> None:
        """Open system file picker dialog using Flet's native FilePicker service."""
        if self._page is None:
            LoggerUtil.get_logger().error("ExplorerUiUtil: not registered with a page")
            return

        async def _async_pick():
            try:
                if self._picker is None:
                    self._picker = ft.FilePicker()

                file_type = (
                    ft.FilePickerFileType.CUSTOM
                    if allowed_extensions
                    else ft.FilePickerFileType.ANY
                )
                files = await self._picker.pick_files(
                    dialog_title="Chọn File",
                    allow_multiple=False,
                    file_type=file_type,
                    allowed_extensions=allowed_extensions,
                )
                if files and len(files) > 0 and files[0].path:
                    path = files[0].path
                    LoggerUtil.get_logger().info(f"ExplorerUiUtil: file selected: {path}")
                    on_result(path)
                else:
                    on_result(None)
            except Exception as e:
                LoggerUtil.get_logger().error(f"ExplorerUiUtil.pick_file error: {e}")
                on_result(None)

        self._page.run_task(_async_pick)

    def show_in_explorer(self, path: str) -> None:
        """Open Windows Explorer and select/highlight the given path."""
        if not path:
            return
        path = os.path.abspath(path)
        try:
            if os.path.isfile(path):
                subprocess.run(["explorer", "/select,", path])
            elif os.path.isdir(path):
                subprocess.run(["explorer", path])
            else:
                LoggerUtil.get_logger().error(f"ExplorerUiUtil.show_in_explorer: path not found: {path}")
        except Exception as e:
            LoggerUtil.get_logger().error(f"ExplorerUiUtil.show_in_explorer error: {e}")


