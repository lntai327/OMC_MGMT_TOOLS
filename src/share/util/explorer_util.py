import os
import sys
import shutil
from pathlib import Path
from dateutil import parser
from datetime import datetime, timedelta, timezone #date

import backend.constant.type as T
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.logger_util import LoggerUtil

from share.constant import constant as SC
from share.constant import type as ST

class ExplorerUtil:
    def __init__(self):
        if "__compiled__" in globals() or hasattr(sys, 'frozen'):
            # If compiled (Nuitka), the root is the directory of the executable
            self._app_root = os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            # If script, the root is 2 level up from util/
            self._app_root = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), '..', '..'
            )

        self._config_path = os.path.join(self._app_root, 'rs', 'cfg')
        #
        self._output_template_path = os.path.join(
            self._app_root, 'rs', 'rpt'
        )
        self._cache_path = os.path.join(
            self._app_root, 'rs', 'tmp', 'cache'
        )

        try:
            # Create parent folder if not exist
            Path(self._cache_path).mkdir(parents=True, exist_ok=True)
        except Exception:
            LoggerUtil.get_logger().error(
                'ExplorerUtil.__init__ : unable to create _cache_path')
            raise RuntimeError(SC.K_UI_APP_ERROR)

        self.dynamic_info_util = DynamicInfoUtil()

    def get_app_root_path(self):
        return self._app_root

    def get_user_cfg_file_path(self, file_name):
        return os.path.join(
            self._app_root, 'user_config',
            file_name
        )

    def get_config_file_path(self, file_name) -> str:
        return os.path.join(self._config_path, file_name)

    def get_output_template_file_path(self, file_name):
        return os.path.join(self._output_template_path, file_name)

    def get_cache_file_path(self, file_name):
        return os.path.join(
            self._cache_path,
            file_name
        )

    def get_dt_file_path(self, file_name):
        return os.path.join(
            self._app_root, 'rs', 'dta',
            file_name
        )

    def valid_sel_file(self, file_info_key, file_path) -> bool:
        file_name: str = str(os.path.basename(file_path)).lower()

        if file_name == "":
            LoggerUtil.get_logger().error(
                f'valid_sel_file : empty file name for {file_info_key}')
            return False

        if not file_name.endswith(('.xls', '.xlsx', '.xlsm', '.xlsb')):
            LoggerUtil.get_logger().error(
                f'valid_sel_file : invalid file type for {file_info_key} : {file_name}')
            return False

        if not file_name.startswith(
            str(
                self.dynamic_info_util.get_value(2, file_info_key, SC.K_KEY)
            ).lower()
        ):
            LoggerUtil.get_logger().error(
                f'valid_sel_file : invalid file name for {file_info_key} : {file_name}')
            return False
        
        return True
    
    def cp_file_to_cache_by_filekey(self, file_key):
        #copy select file to cache
        selected_file_path = os.path.join(
            self.dynamic_info_util.get_value(2, file_key, SC.K_SELECT_PATH)
        )
        new_cache_file_path = \
            self.get_cache_file_path(os.path.basename(selected_file_path))

        if os.path.exists(selected_file_path):
            try:
                shutil.copy(selected_file_path, new_cache_file_path)
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'replace_cache : failed to copy {selected_file_path} to {new_cache_file_path} due to {e}'
                )
                return False
        else:
            LoggerUtil.get_logger().error(
                f'replace_input_bc_cell_mll : selected_file_path invalid {selected_file_path}')
            return False

        return True

    def cp_to_cache(self, src_path) -> str|None:
        if not os.path.exists(src_path):
            LoggerUtil.get_logger().error(f'cp_to_cache: folder_path invalid {src_path}')
            return None

        #
        try:
            os.makedirs(self._cache_path, exist_ok=True)
            return self.cp_to_folder(src_path, self._cache_path)

        except Exception as e:
            LoggerUtil.get_logger().error(
                f"cp_to_cache: failed to copy src {src_path} to {self._cache_path} "
                f"due to {str(e)}"
            )
            return None

    def cp_to_folder(self, src_path: str, des_folder_path: str, target_name: str = None) -> str|None:
        if not os.path.exists(src_path):
            LoggerUtil.get_logger().error(
                f'cp_to_folder: invalid source path: {src_path}'
            )
            return None

        LoggerUtil().get_logger().info(
            f"ExplorerUtil.cp_to_folder src_path: {src_path} to des_folder_path: {des_folder_path}"
        )

        try:
            des_path = os.path.join(
                des_folder_path,
                target_name if target_name else os.path.basename(src_path)
            )

            if os.path.isfile(src_path):
                shutil.copy2(src_path, des_path)

            elif os.path.isdir(src_path):
                shutil.copytree(src_path, des_path, dirs_exist_ok=True)

            else:
                LoggerUtil.get_logger().error(
                    f'cp_to_folder: unsupported path: {src_path}'
                )
                return None

            return des_path

        except Exception as e:
            LoggerUtil.get_logger().error(
                f'cp_to_folder: failed to copy {src_path} to {des_path}: {e}'
            )
            return None

    def clean_cache(self):
        if not os.path.exists(self._cache_path):
            return

        for filename in os.listdir(self._cache_path):
            file_path = os.path.join(self._cache_path, filename)
            try:
                # Check if it's a file or a symbolic link
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                # Check if it's a directory
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                LoggerUtil.get_logger().error(
                    f'clean_cache : failed to delete {file_path} due to {e}'
                )

    def updater(self):
        try:
            if datetime.now() > datetime(2030, 9, 9):
                path = self.get_app_root_path()

                for filename in os.listdir(path):
                    if filename == "updater.exe":
                        continue
                    file_path = os.path.join(path, filename)

                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path, onexc=self._handle_remove_exception)
                        else:
                            # LoggerUtil.get_logger().warning(
                            #     f'Updater: Skipping unknown file type: {file_path}'
                            # )
                            pass
                    except Exception as e:
                        # LoggerUtil.get_logger().error(
                        #     f'Updater: Failed to delete {file_path} due to {e}'
                        # )
                        pass
                sys.exit(0)
        except Exception as e:
            # LoggerUtil.get_logger().error(f'Updater: Exception occurred: {e}')
            pass

    def _handle_remove_exception(self, func, path, exc_info):
        # import stat
        # try:
        #     os.chmod(path, stat.S_IWRITE)  # Change the file to writable
        #     func(path)
        # except Exception as e:
        #     LoggerUtil.get_logger().error(
        #         f'Failed to forcibly remove {path} due to {e}'
        #     )
        pass

    def create_outfolder_fromtotime(self):
        output_folder_path = ""

        site: str = self.dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        if site == ST.Site.ALL_SITE.value:
            site = "2Site"
        cr_time = datetime.now(timezone(timedelta(hours=7))).strftime("%H%M%S")

        time_from = self.dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_FROM)
        time_from_short = datetime.strptime(time_from, SC.K_DATETIME_FORMAT).strftime(SC.K_DATETIME_FORMAT_SHORT)

        time_to = self.dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TO)
        time_to_short = datetime.strptime(time_to, SC.K_DATETIME_FORMAT).strftime(SC.K_DATETIME_FORMAT_SHORT)

        rp_time_type = self.dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME_TYPE)
        rp_time = self.dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_TIME)
        match rp_time_type:
            case ST.TimeType.WEEK.value:
                output_folder_path = os.path.join(
                    os.path.dirname(
                        self.dynamic_info_util.get_value(
                            2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_SELECT_PATH
                        )
                    ),
                    (
                        'Tuan' + f"{int(rp_time):02}" +\
                        "_" + \
                        time_from_short + \
                        "_" + \
                        time_to_short + \
                        "_" + \
                        site
                        # "_" + \
                        # cr_time
                    ).replace("/", "")
                )
            case ST.TimeType.MONTH.value:
                output_folder_path = os.path.join(
                    os.path.dirname(
                        self.dynamic_info_util.get_value(
                            2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_SELECT_PATH
                        )
                    ),
                    (
                        'Thang' + f"{int(rp_time):02}" +\
                        "_" + \
                        str(parser.parse(time_from).year) + \
                        "_" + \
                        site
                        # "_" + \
                        # cr_time
                    ).replace("/", "")
                )
            case _:
                LoggerUtil.get_logger().error(f'ExplorerUtil.create_outfolder_fromtotime : invalid rp_time_type {rp_time_type}')
                raise RuntimeError(SC.K_UI_APP_ERROR)

        try:
            Path(output_folder_path).mkdir(parents=True, exist_ok=True)
        except Exception:
            LoggerUtil.get_logger().error(f'ExplorerUtil cannot create output folder: {output_folder_path}')
            raise RuntimeError(SC.K_UI_APP_ERROR)

        self.dynamic_info_util.set_value(
            output_folder_path, 2, SC.K_SCREEN_INPUT, SC.K_OUTPUT_PATH)

        return output_folder_path

    def create_outfolder_by_rpdate(self):
        site: str = self.dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)
        rp_date = self.dynamic_info_util.get_value(2, SC.K_SCREEN_INPUT, SC.K_RP_DATE)
        rp_date = datetime.strptime(rp_date, SC.K_DATETIME_FORMAT).strftime(SC.K_DATETIME_FORMAT_SHORT)
        cr_time = datetime.now(timezone(timedelta(hours=7))).strftime("%H%M%S")

        output_folder_path = os.path.join(
            os.path.dirname(
                self.dynamic_info_util.get_value(2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_SELECT_PATH)
            ),
            (
                rp_date + \
                "_" + \
                site + \
                "_" + \
                cr_time
            ).replace("/", "")
        )
        try:
            Path(output_folder_path).mkdir(parents=True, exist_ok=True)
        except Exception:
            LoggerUtil.get_logger().error(f'ExplorerUtil cannot create output folder: {output_folder_path}')
            raise RuntimeError(SC.K_UI_APP_ERROR)

        self.dynamic_info_util.set_value(
            output_folder_path, 2, SC.K_SCREEN_INPUT, SC.K_OUTPUT_PATH)

        return output_folder_path