"""Windows Credential Manager helper using keyring."""

import keyring

from share.util.logger_util import LoggerUtil

class WinCredential:
    def __init__(self):
        self.service_name = "omc_report_tool"

    def save_db_password(self, username: str, password: str) -> bool:
        """Save a DB password to Windows Credential Manager.

        Args:
            service_name: The keyring service identifier (from db_cf.keyring_service_name).
            username: The DB username used as the credential account name.
            password: The plain-text password to store.

        Returns:
            True on success, False on failure.
        """
        try:
            keyring.set_password(self.service_name, username, password)
            return True
        except Exception as e:
            LoggerUtil.get_logger().error(f'win_credential_manage save_db_password failed: {e}')
            return False


    def get_db_password(self, username: str) -> str | None:
        """Retrieve a DB password from Windows Credential Manager.

        Args:
            service_name: The keyring service identifier (from db_cf.keyring_service_name).
            username: The DB username used as the credential account name.

        Returns:
            The stored password string, or None if not found / on error.
        """
        try:
            return keyring.get_password(self.service_name, username)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'win_credential_manage get_db_password failed: {e}'
                f' service_name: {self.service_name}'
                f' username: {username}'
            )
            return None
