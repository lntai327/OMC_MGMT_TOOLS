import os
import json
import time
import tempfile
import threading

from share.util.logger_util import LoggerUtil
from share.constant import constant as SC

class DynamicInfoUtil:
    _lock = threading.Lock()

    def __init__(self):
        self.dynamic_info = None
        self._mtime = None
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self._excel_dynamic_info_path = os.path.join(
            current_dir, '..', '..', 'rs', 'cfg', SC.K_FILE_DYNAMIC_INFO)

        self._load()

    def _load(self):
        if not os.path.exists(self._excel_dynamic_info_path):
            LoggerUtil.get_logger().error(
                f'DynamicInfoUtil._load : dynamic info file not found at {self._excel_dynamic_info_path}'
            )
            raise RuntimeError('DynamicInfoUtil._load : dynamic info not found')

        max_retries = 3
        for attempt in range(max_retries):
            try:
                mtime = os.path.getmtime(self._excel_dynamic_info_path)
                with open(self._excel_dynamic_info_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.dynamic_info = data
                self._mtime = mtime
                return
            except (json.JSONDecodeError, ValueError):
                if attempt < max_retries - 1:
                    time.sleep(0.1)
                    continue
                LoggerUtil.get_logger().error(
                    'DynamicInfoUtil._load : JSON file is empty or corrupt after retries'
                )
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'DynamicInfoUtil._load : unable to load dynamic info file due to {e}'
                )
                return

    def _reload_if_changed(self):
        try:
            mtime = os.path.getmtime(self._excel_dynamic_info_path)
            if self._mtime is None or mtime != self._mtime:

                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        with open(self._excel_dynamic_info_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        self.dynamic_info = data
                        self._mtime = mtime
                        return
                    except (json.JSONDecodeError, ValueError):
                        if attempt < max_retries - 1:
                            time.sleep(0.1)
                            continue
                        LoggerUtil.get_logger().error(
                            'DynamicInfoUtil._reload_if_changed : JSON file is empty or corrupt after retries'
                        )
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'DynamicInfoUtil._reload_if_changed : unable to reload dynamic info file due to {e}'
            )

    def get_all(self):
        with DynamicInfoUtil._lock:
            self._reload_if_changed()
            return self.dynamic_info

    def get_value(self, numkey, key1=None, key2=None, key3=None, key4=None):
        with DynamicInfoUtil._lock:
            self._reload_if_changed()

            try:
                match numkey:
                    case 1:
                        return self.dynamic_info[key1]
                    case 2:
                        return self.dynamic_info[key1][key2]
                    case 3:
                        return self.dynamic_info[key1][key2][key3]
                    case 4:
                        return self.dynamic_info[key1][key2][key3][key4]
                    case _:
                        return None
            except Exception as e:
                LoggerUtil.get_logger().error(f"DynamicInfoUtil get_value {e}")
                return None


    def set_value(self, value, numkey, key1=None, key2=None, key3=None, key4=None):
        with DynamicInfoUtil._lock:
            self._reload_if_changed()
            match numkey:
                case 1:
                    self.dynamic_info[key1] = value
                case 2:
                    self.dynamic_info[key1][key2] = value
                case 3:
                    self.dynamic_info[key1][key2][key3] = value
                case 4:
                    self.dynamic_info[key1][key2][key3][key4] = value
                case _:
                    return None

            dir_name = os.path.dirname(self._excel_dynamic_info_path)
            try:
                fd, tmp_path = tempfile.mkstemp(
                    dir=dir_name, suffix='.tmp', prefix='.dynamic_info_')
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as f:
                        json.dump(self.dynamic_info, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_path, self._excel_dynamic_info_path)
                except BaseException:

                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    raise
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'DynamicInfoUtil.set_value : unable to save dynamic info file due to {e}')
                return

            try:
                self._mtime = os.path.getmtime(self._excel_dynamic_info_path)
            except Exception:
                LoggerUtil.get_logger().error(
                    'DynamicInfoUtil.set_value : unable to update mtime after saving dynamic info file')

    def update_selected_excel_info(self, file_info_key: str, file_path: str):
        required_sheets = DynamicInfoUtil().get_value(
            2, file_info_key, SC.K_REQUIRE_SHEET
        )
        try:
            self.set_value(file_path, 2, file_info_key, SC.K_SELECT_PATH)
            file_name = os.path.basename(file_path)
            self.set_value(file_name, 2, file_info_key, SC.K_NAME)
            self.set_value("1", 2, file_info_key, SC.K_SELECT)

            from backend.util.ex_handle_util import ExcelHandleUtil
            all_found = True
            for sheet_key, v in required_sheets.items():
                sheet_name: list[str] = ExcelHandleUtil().get_sheet_dynamic_name(
                    file_info_key, file_path, sheet_key
                )
                if sheet_name:
                    self.set_value(sheet_name, 4, file_info_key,
                                    SC.K_REQUIRE_SHEET, sheet_key,
                                    SC.K_NAME
                    )
                else:
                    all_found = False

            if all_found:
                return True

            LoggerUtil.get_logger().error(
                'DynamicInfoUtil.update_selected_excel_info : required sheet not found')
            self.set_value("0", 2, file_info_key, SC.K_SELECT)

            return False
        except Exception as e:
            LoggerUtil.get_logger().error(f"DynamicInfoUtil update_selected_excel_info {e}")
            self.set_value("0", 2, file_info_key, SC.K_SELECT)

            return False