import os
import json
from openpyxl import load_workbook

from share.util.logger_util import LoggerUtil
from share.constant import constant as SC

class DynamicInfoUtil:
    def __init__(self):
        self.dynamic_info = None
        self._mtime = None
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self._excel_dynamic_info_path = os.path.join(
            current_dir, '..', '..', 'rs', 'cfg', SC.K_FILE_DYNAMIC_INFO)
        # load file once during init
        self._load()

    def _load(self):
        if not os.path.exists(self._excel_dynamic_info_path):
            LoggerUtil.get_logger().error(
                f'DynamicInfoUtil._load : dynamic info file not found at {self._excel_dynamic_info_path}'
            )
            raise RuntimeError('DynamicInfoUtil._load : dynamic info not found')

        try:
            mtime = os.path.getmtime(self._excel_dynamic_info_path)
            with open(self._excel_dynamic_info_path, 'r', encoding='utf-8') as f:
                self.dynamic_info = json.load(f)
            self._mtime = mtime
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'DynamicInfoUtil._load : unable to load dynamic info file due to {e}')

    def _reload_if_changed(self):
        try:
            mtime = os.path.getmtime(self._excel_dynamic_info_path)
            if self._mtime is None or mtime != self._mtime:
                with open(self._excel_dynamic_info_path, 'r', encoding='utf-8') as f:
                    self.dynamic_info = json.load(f)
                self._mtime = mtime
        except Exception:
            # ignore reload errors and keep last known good value
            LoggerUtil.get_logger().error(
                'DynamicInfoUtil._reload_if_changed : unable to reload dynamic info file')

    def get_all(self):
        # ensure we have the latest on disk
        self._reload_if_changed()
        return self.dynamic_info

    def get_value(self, numkey, key1=None, key2=None, key3=None, key4=None):
        # ensure we have the latest on disk
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

        with open(self._excel_dynamic_info_path, 'w', encoding='utf-8') as f:
            json.dump(self.dynamic_info, f, indent=2, ensure_ascii=False)

        # update stored mtime so subsequent reads know file is current
        try:
            self._mtime = os.path.getmtime(self._excel_dynamic_info_path)
        except Exception:
            LoggerUtil.get_logger().error(
                'DynamicInfoUtil.set_value : unable to update mtime after saving dynamic info file')

    def update_selected_excel_info(self, file_info_key: str, file_path: str):
        required_sheets = DynamicInfoUtil().get_value(2, file_info_key, SC.K_REQUIRE_SHEET)
        try:
            self.set_value(file_path, 2, file_info_key, SC.K_SELECT_PATH)
            file_name = os.path.basename(file_path)
            self.set_value(file_name, 2, file_info_key, SC.K_NAME)
            self.set_value("1", 2, file_info_key, SC.K_SELECT)

            from backend.util.excel_loader_util import ExcelLoaderUtil
            for sheet_key, v in required_sheets.items():
                sheet_name = ExcelLoaderUtil().get_sheet_dynamic_name(
                    file_info_key, file_path, sheet_key
                )
                if sheet_name:
                    self.set_value(sheet_name, 4, file_info_key,
                                    SC.K_REQUIRE_SHEET, sheet_key,
                                    SC.K_NAME
                    )
                    return True
            LoggerUtil.get_logger().error(
                'DynamicInfoUtil.update_selected_excel_info : required sheet not found')
            self.set_value("0", 2, file_info_key, SC.K_SELECT)

            return False
        except Exception as e:
            LoggerUtil.get_logger().error(f"DynamicInfoUtil update_selected_excel_info {e}")
            self.set_value("0", 2, file_info_key, SC.K_SELECT)

            return False