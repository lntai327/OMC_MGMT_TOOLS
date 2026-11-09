"""LoginViewModel — authentication logic for the Login page."""
from share.util.logger_util import LoggerUtil
from share.session import Session
from backend.repositories.account.account import AccountService
from frontend.viewmodels.base_vm import BaseViewModel


class LoginViewModel(BaseViewModel):
    """ViewModel for the Login page.

    Observable keys:
        "error_message"  — inline error text (empty = no error)
        "is_loading"     — True while authenticating
    """

    def __init__(self, on_login_success=None):
        """
        Args:
            on_login_success: Callable(role: str) called after successful login.
        """
        super().__init__()
        self._username: str = ""
        self._password: str = ""
        self._error_message: str = ""
        self._is_loading: bool = False
        self._on_login_success = on_login_success
        self._account_service = AccountService()

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        self._username = value

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, value: str):
        self._password = value

    @property
    def error_message(self) -> str:
        return self._error_message

    @error_message.setter
    def error_message(self, value: str):
        self._error_message = value
        self.notify("error_message")

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @is_loading.setter
    def is_loading(self, value: bool):
        self._is_loading = value
        self.notify("is_loading")

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def login(self) -> bool:
        """Authenticate with username/password.

        Returns True on success; sets error_message on failure.
        """
        username = self._username.strip()
        password = self._password.strip()

        if not username or not password:
            self.error_message = "Nhập tài khoản và mật khẩu"
            return False

        self.is_loading = True
        self.error_message = ""
        try:
            role = self._account_service.app_authenticate(username, password)
        except Exception as e:
            LoggerUtil.get_logger().error(f"LoginViewModel.login failed: {e}")
            self.error_message = "Lỗi đăng nhập"
            self.is_loading = False
            return False
        finally:
            self.is_loading = False

        if role:
            Session.set_role(role)
            if callable(self._on_login_success):
                self._on_login_success(role)
            return True
        else:
            self.error_message = "Sai tài khoản hoặc mật khẩu"
            return False

    def guest_login(self):
        """Bypass authentication as guest."""
        Session.set_role("guest")
        if callable(self._on_login_success):
            self._on_login_success("guest")
