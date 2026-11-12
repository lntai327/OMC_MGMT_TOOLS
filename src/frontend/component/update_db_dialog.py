import os
from typing import Callable, Optional

import flet as ft

from backend.services.db_update import DbUpdate
from backend.util.ex_handle_util import ExcelHandleUtil
from backend.constant import excel_struct_info as ESI
from frontend.component.explorer_ui_util import ExplorerUiUtil
from frontend.component.background_task import run_background_task
from share.constant import type as ST
from share.constant import constant as SC
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil


class UpdateDbDialog:
    """Modal dialog for selecting Excel files and updating the database.

    Usage:
        dlg = UpdateDbDialog(page, db_need_update_list)
        dlg.open()
    """

    def __init__(self, page: ft.Page, db_need_update_list: list[str],
                 on_db_updated: Optional[Callable] = None):
        self._page = page
        self._db_need_update_list = db_need_update_list
        self._selected_file_dict: dict[str, str] = {}
        self._on_db_updated: Optional[Callable] = on_db_updated
        self._dynamic_info_util = DynamicInfoUtil()
        self._explorer_util = ExplorerUtil()
        self._explorer_ui_util = ExplorerUiUtil()
        self._explorer_ui_util.register(page)

        self._is_loading: bool = False
        self._cancel_requested: bool = False
        self._explicit_closed: bool = False

        # Build file rows
        self._path_fields: dict[str, ft.TextField] = {}
        file_rows: list[ft.Control] = []

        for key in db_need_update_list:
            field = ft.TextField(
                value="",
                read_only=True,
                dense=True,
                expand=True,
                hint_text=ESI.EXCEL_STRUCT_INFO.get(key, {}).get("hint", ""),
                hint_style=ft.TextStyle(
                    color=ft.Colors.GREY_500,
                ),
            )
            self._path_fields[key] = field

            try:
                file_name = ST.FileInfoDict.get(key).file_name
            except:
                file_name = key

            file_rows.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(file_name, size=11, no_wrap=False),
                            width=120,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            tooltip=SC.K_UI_SEL,
                            on_click=lambda _, k=key: self._pick_file(k),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            tooltip=SC.K_UI_CLEAR,
                            on_click=lambda _, k=key: self._clear_file(k),
                        ),
                        field,
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        self._status_text = ft.Text("", size=12, no_wrap=False, expand=True)
        self._progress = ft.ProgressRing(visible=False, width=20, height=20)

        self._btn_update_db = ft.Button(
            content=ft.Text(SC.K_UI_UPDATE_DB),
            on_click=lambda _: self._start_update(),
            width=320,
            height=44,
            # bgcolor=ft.Colors.PRIMARY,
            # color=ft.Colors.ON_PRIMARY,
        )

        self._dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text(SC.K_UI_UPDATE_DB, weight=ft.FontWeight.W_600),
            on_dismiss=self._on_dialog_dismiss,
            content=ft.Column(
                controls=[
                    *file_rows,
                    ft.Divider(),
                    ft.Row([self._progress, self._status_text], spacing=8),
                    ft.Container(height=8),
                    ft.Row(
                        [
                            self._btn_update_db
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            ft.TextButton(
                                content=ft.Text(SC.K_UI_CANCEL),
                                on_click=lambda _: self.close(),
                                width=320,
                                height=44,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                width=700,
                tight=True,
            ),
        )
        page.overlay.append(self._dialog)

    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #

    def _reset_state(self):
        self._status_text.value = ""
        self._status_text.visible = False

        self._page.update()

    def open(self):
        # Reset state
        for key, field in self._path_fields.items():
            field.value = ""
        self._selected_file_dict.clear()
        self._reset_state()
        self._explicit_closed = False
        self._dialog.modal = False
        self._dialog.open = True
        self._page.update()

    def close(self):
        self._explicit_closed = True
        if self._is_loading:
            self._cancel_requested = True
        self._dialog.open = False
        self._page.update()

    def _on_dialog_dismiss(self, e):
        if self._is_loading and not self._explicit_closed:
            self._dialog.open = True
            self._page.update()

    # ------------------------------------------------------------------ #
    # File selection
    # ------------------------------------------------------------------ #

    def _pick_file(self, key: str):
        def _on_result(path: Optional[str]):
            if not path:
                return
            if self._explorer_util.valid_sel_file(key, path) is False:
                file_name: str = str(os.path.basename(path)).lower()
                if file_name.endswith('.xls'):
                    new_format_file_path = ExcelHandleUtil().convert_old_xls_to_xlsx(path)
                    self._status_text.value = (
                        f"Đầu vào quá cũ, Convert .xls->.xlsx: {path}"
                        f" ,hãy kiểm tra file convert và chọn lại file format mới"
                    )
                else:
                    self._status_text.value = f"{SC.K_UI_INVALID}: {key}"

                self._status_text.color = ft.Colors.ERROR
                self._status_text.visible = True
                self._page.update()
                return
            self._selected_file_dict[key] = path
            self._path_fields[key].value = path
            self._path_fields[key].update()

        self._reset_state()

        self._explorer_ui_util.pick_file(
            on_result=_on_result,
            allowed_extensions=["xlsx", "xls"]
        )

    def _clear_file(self, key: str):
        self._selected_file_dict.pop(key, None)
        self._path_fields[key].value = ""
        self._path_fields[key].update()

    # ------------------------------------------------------------------ #
    # DB update task
    # ------------------------------------------------------------------ #

    def _start_update(self):
        if self._is_loading:
            return
        
        self._reset_state()

        if not self._selected_file_dict:
            self._status_text.value = SC.K_UI_NO_SEL_FILE
            self._status_text.color = ft.Colors.ERROR
            self._status_text.visible = True

            self._page.update()
            return

        self._is_loading = True
        self._cancel_requested = False
        self._explicit_closed = False
        self._dialog.modal = True
        self._btn_update_db.disabled = True
        self._btn_update_db.update()
        self._progress.visible = True
        self._status_text.value = SC.K_UI_LOADING_TEXT
        self._status_text.visible = True
        self._page.update()

        def _task() -> bool:
            db_update = DbUpdate()
            try:
                for file_key in self._db_need_update_list:
                    if self._cancel_requested:
                        return False
                    if file_key not in self._selected_file_dict:
                        continue
                    path = self._selected_file_dict[file_key]
                    if self._dynamic_info_util\
                            .update_selected_excel_info(file_key, path) is False:
                        LoggerUtil.get_logger().error(f"UpdateDbDialog: invalid file {file_key}")
                        raise RuntimeError(f"UpdateDbDialog: invalid file {file_key}")

                    if self._cancel_requested:
                        return False

                    self._selected_file_dict.pop(file_key, None)
                    if self._dynamic_info_util.get_value(2, file_key, SC.K_SELECT) != "1":
                        continue
                    self._explorer_util.cp_file_to_cache_by_filekey(file_key)

                    import os
                    sel_name = os.path.basename(
                        self._dynamic_info_util.get_value(2, file_key, SC.K_SELECT_PATH) or ""
                    )
                    self._dynamic_info_util.set_value(sel_name, 2, file_key, SC.K_NAME)
                    self._dynamic_info_util.set_value("0", 2, file_key, SC.K_SELECT)

                    if self._cancel_requested:
                        return False

                    if db_update.update_db(file_key) is False:
                        return False
                return True
            except Exception as e:
                LoggerUtil.get_logger().error(f"{self.__class__.__name__} error: {e}")
                return False

        def _finish(success: bool):
            self._is_loading = False
            self._dialog.modal = False
            self._progress.visible = False
            self._btn_update_db.disabled = False
            self._btn_update_db.update()
            if self._cancel_requested:
                self._status_text.value = "Đã hủy cập nhật"
                self._status_text.color = ft.Colors.ORANGE
                self._status_text.visible = True
            elif success:
                self._status_text.value = "Cập nhật thành công"
                self._status_text.color = ft.Colors.GREEN
                self._status_text.visible = True
                # Reset file fields
                for key, field in self._path_fields.items():
                    field.value = ""

                if self._on_db_updated:
                    try:
                        self._on_db_updated()
                    except Exception as _e:
                        LoggerUtil.get_logger().error(f"UpdateDbDialog on_db_updated callback error: {_e}")
            else:
                self._status_text.value = "Cập nhật thất bại"
                self._status_text.color = ft.Colors.ERROR
                self._status_text.visible = True
            self._page.update()

        # Use page.run_thread — page.update() is thread-safe in Flet 0.86
        def _worker():
            result = _task()
            _finish(result)
        self._page.run_thread(_worker)
