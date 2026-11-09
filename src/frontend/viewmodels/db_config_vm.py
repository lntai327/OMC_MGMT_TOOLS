from backend.db.sqlserver import SqlServer
from backend.db.database import Database
from backend.db.win_credential import WinCredential
from frontend.viewmodels.base_vm import BaseViewModel

from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import constant as SC


class DbConfigViewModel(BaseViewModel):
    """ViewModel for DB connection check and configuration.

    Observable keys:
        "status_message"  — human-readable status text
        "is_loading"      — True while checking connection
        "is_connected"    — True after a successful check
    """

    def __init__(self):
        super().__init__()
        self._status_message: str = "Đang kiểm tra kết nối CSDL..."
        self._is_loading: bool = False
        self._is_connected: bool = False

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def status_message(self) -> str:
        return self._status_message

    @status_message.setter
    def status_message(self, value: str):
        self._status_message = value
        self.notify("status_message")

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @is_loading.setter
    def is_loading(self, value: bool):
        self._is_loading = value
        self.notify("is_loading")

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @is_connected.setter
    def is_connected(self, value: bool):
        self._is_connected = value
        self.notify("is_connected")

    # ------------------------------------------------------------------ #
    # DB config accessors
    # ------------------------------------------------------------------ #

    def get_db_config(self) -> dict:
        """Return current DB config dict (server, db, username)."""
        return SqlServer().get_db_config()

    def save_config(self, server: str, db: str, username: str, password: str) -> bool:
        """Persist server/db/username to dynamic_info.json and password to keyring.

        Returns True on success.
        """
        try:
            dynamic_info = DynamicInfoUtil()
            db_cf = dynamic_info.get_value(1, SC.K_DB_CF) or {}
            variant = db_cf.get(SC.K_VARIANT, 'default')

            # Use the structured path
            dynamic_info.set_value(server, 3, SC.K_DB_CF, variant, SC.K_SERVER)
            dynamic_info.set_value(db, 3, SC.K_DB_CF, variant, SC.K_DB)
            dynamic_info.set_value(username, 3, SC.K_DB_CF, variant, SC.K_USERNAME)

            ok = WinCredential().save_db_password(username, password)
            if not ok:
                LoggerUtil.get_logger().error("DbConfigViewModel.save_config: failed to save password")
                return False
            return True
        except Exception as e:
            LoggerUtil.get_logger().error(f"DbConfigViewModel.save_config failed: {e}")
            return False

    # ------------------------------------------------------------------ #
    # Connection check
    # ------------------------------------------------------------------ #

    def check_connection(self,
            user: str = None, password: str = None) -> bool:
        """Try to connect and run SELECT 1 against the configured DB.

        Updates is_loading, status_message, is_connected.
        Returns True on success.
        """
        self.is_loading = True
        self.status_message = "Đang kiểm tra kết nối CSDL..."
        try:
            LoggerUtil.get_logger().info("DbConfigViewModel: checking DB connection...")
            ret = Database().test_connection(user, password)
            if ret is True:
                self.is_connected = True
                self.status_message = "Kết nối CSDL thành công"
                LoggerUtil.get_logger().info("DbConfigViewModel: DB connection OK")
                return True
            else:
                self.is_connected = False
                self.status_message = f"Kết nối CSDL thất bại."
                LoggerUtil.get_logger().error(
                    f"DbConfigViewModel: DB connection failed")
                return False
        except Exception as e:
            self.is_connected = False
            self.status_message = f"Kết nối CSDL thất bại"
            LoggerUtil.get_logger().error(
                f"DbConfigViewModel.check_connection failed: {e}")
            return False
        finally:
            self.is_loading = False
