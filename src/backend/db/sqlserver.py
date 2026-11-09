import pyodbc
from urllib.parse import quote_plus
from pubsub import pub

from backend.db.win_credential import WinCredential

from share.util.logger_util import LoggerUtil
from share.constant import constant as SC
from share.util.dynamic_info_util import DynamicInfoUtil

class SqlServer:
    """Builds and manages a SQLAlchemy engine for SQL Server (pyodbc).
    Config is injected at construction time — no file I/O here.
    """

    def __init__(self):
        db_cf = self.get_db_config()
        self._server = db_cf.get(SC.K_SERVER, '')
        self._database = db_cf.get(SC.K_DB, '')
        self._username = db_cf.get(SC.K_USERNAME, '')
        self._password = WinCredential().get_db_password(self._username)

        if self._password is None:
            LoggerUtil.get_logger().error(f"SQL Server credentials not found: {db_cf}")
            # raise RuntimeError("SQL Server credentials not found")

        # Dynamically detect installed SQL Server ODBC drivers
        self._driver = "SQL Server"

        available_drivers = pyodbc.drivers()
        preferred_drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ]
        for pd in preferred_drivers:
            if pd in available_drivers:
                self._driver = pd
                break

        LoggerUtil.get_logger().info(
            f"SqlServer: select driver: {self._driver}"
        )

    def get_db_config(self) -> dict:
        db_cf = DynamicInfoUtil().get_value(1, SC.K_DB_CF) or {}
        variant = db_cf.get(SC.K_VARIANT, '')
        variant_cfg = db_cf.get(variant, {})
        return {
            SC.K_VARIANT: variant,
            SC.K_SERVER: variant_cfg.get(SC.K_SERVER, ''),
            SC.K_DB: variant_cfg.get(SC.K_DB, ''),
            SC.K_USERNAME: variant_cfg.get(SC.K_USERNAME, ''),
        }

    def build_db_connection_string(
        self,
        user: str = None,
        password: str = None
    ) -> str:
        """Build SQLAlchemy connection string."""
        if not user or not password:
            user = user or self._username
            password = password or self._password

        params = [
            f"DRIVER={self._driver}",
            f"SERVER={self._server}",
            f"DATABASE={self._database}",
            f"UID={user}",
            f"PWD={password}",
        ]
        # For modern drivers, disable Encrypt and trust certificate
        # to prevent connection failures due to self-signed certs or default driver encryption settings.
        if "ODBC Driver" in self._driver:
            params.append("TrustServerCertificate=yes")
            params.append("Encrypt=no")

        odbc_str = ";".join(params)
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"