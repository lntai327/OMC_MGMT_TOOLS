from backend.db.database import Database
from backend.db.sqlserver import SqlServer
from backend.db.win_credential import WinCredential
from backend.models.account import AccountModel
from backend.services.secure import hash_password

from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.logger_util import LoggerUtil
from share.constant import constant as SC

class AccountRepo:
    """Low-level account queries against the 'account' table."""

    def find_by_credentials(self, session, username: str, hashed_password: str) -> AccountModel | None:
        """Return the AccountModel whose username and hashed password match, or None.

        Args:
            session:         An open SQLAlchemy Session.
            username:        The username to look up.
            hashed_password: SHA-256 hex digest of the raw password.

        Returns:
            Matching AccountModel instance, or None.
        """
        return (
            session.query(AccountModel)
            .filter(
                AccountModel.username == username,
                AccountModel.password == hashed_password,
            )
            .first()
        )

class AccountService:
    """Application-level account service.

    Reads DB connection config from dynamic_info.json (db_cf section),
    retrieves the password from Windows Credential Manager, and delegates
    query logic to AccountRepo.
    """

    def __init__(self):
        self._dynamic_info = DynamicInfoUtil()
        self._repository = AccountRepo()

    # ------------------------------------------------------------------
    # Public helpers — used by the DB Account popup
    # ------------------------------------------------------------------

    def save_db_account(self, username: str, password: str) -> bool:
        """Persist the DB username to dynamic_info.json and the password to the Credential Manager.

        Args:
            username: The DB login username.
            password: The plain-text DB password.

        Returns:
            True on full success, False if either save step failed.
        """
        db_cf = SqlServer().get_db_config() or {}
        variant = db_cf.get(SC.K_VARIANT, '')
        keyring_service = db_cf.get(SC.K_KEYRING_SERVICE, '')

        if not variant:
            LoggerUtil.get_logger().error(
                'AccountService.save_db_account: missing variant db_cf'
            )
            return False

        # 1. Save username to dynamic_info.json
        self._dynamic_info.set_value(
            username, 3,
            SC.K_DB_CF, variant, SC.K_USERNAME,
        )

        # 2. Save password to Windows Credential Manager
        ok = WinCredential().save_db_password(username, password)
        if not ok:
            LoggerUtil.get_logger().error(
                'AccountService.save_db_account: failed to save password to Credential Manager'
            )
        return ok

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def app_authenticate(self, username: str, password: str) -> str | None:
        """Authenticate a user against the DB account table.

        Reads server/db from dynamic_info.json, password from Credential
        Manager, then queries the account table.  Saves the last-used
        username back to dynamic_info.json on success.

        Args:
            username: Plain-text username entered by the user.
            password: Plain-text password entered by the user.

        Returns:
            The user's role string on success, or None on failure.
        """
        hashed = hash_password(password)
        role = None

        db = Database()
        try:
            with db.get_session() as session:
                account = self._repository.find_by_credentials(session, username, hashed)
                if account:
                    role = account.role
        except Exception as e:
            LoggerUtil.get_logger().error(f'AccountService.app_authenticate failed: {e}')
            raise
        finally:
            db.dispose()

        # db_cf = self._dynamic_info.get_value(1, SC.K_DB_CF) or {}
        # variant = db_cf.get(SC.K_VARIANT, '')
        # Persist the last-used username on successful login
        # if role:
        #     try:
        #         self._dynamic_info.set_value(
        #             username, 3,
        #             SC.K_DB_CF, variant, SC.K_USERNAME,
        #         )
        #     except Exception as e:
        #         LoggerUtil.get_logger().warning(
        #             f'AccountService.app_authenticate: failed to save last-used username: {e}'
        #         )

        return role
