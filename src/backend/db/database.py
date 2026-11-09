from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import contextmanager

from backend.db.sqlserver import SqlServer

from share.util.logger_util import LoggerUtil

Base = declarative_base()

class Database:
    def __init__(self):
        self.engine = self._get_engine()
        self.session_local = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False, expire_on_commit=False)

    def _get_engine(self, conn_str: str = None):
        if not conn_str:
            conn_str = SqlServer().build_db_connection_string()

        return create_engine(
            conn_str,
            echo=False,
            pool_pre_ping=True,
            connect_args={"timeout": 15},
            # Disable setinputsizes to avoid HY104 "Invalid precision value" error when using the legacy "SQL Server" ODBC driver with NVARCHAR(MAX) parameters.
            use_setinputsizes=False,
            fast_executemany=True,
        )

    @contextmanager
    def get_session(self):
        """Yield a SQLAlchemy Session, closing engine after use."""
        session: Session = self.session_local()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        else:
            session.commit() #called only when no exception occurred
        finally:
            session.close()

    def get_raw_connection(self):
        """Return a raw DBAPI (pyodbc) connection from the engine.

        The caller is responsible for closing the connection.
        With NullPool the connection is closed immediately on .close().
        """
        return self.engine.raw_connection()

    def dispose(self):
        """Dispose the underlying engine connection pool."""
        try:
            self.engine.dispose()
        except Exception as e:
            LoggerUtil.get_logger().error(f'SqlServer dispose failed: {e}')

    def update_database_engine(self, conn_str: str = None) -> None:
        """Re-create the global engine and SessionLocal sessionmaker with updated connection settings."""
        old_engine = self.engine

        self.engine = self._get_engine(conn_str)
        self.session_local.configure(bind=self.engine)

        if old_engine is not None:
            old_engine.dispose()

    def test_connection(self, user: str = None, password: str = None):
        """Test connecting to SQL Server with given credentials."""
        conn_str = SqlServer().build_db_connection_string(user, password)
        test_eng = create_engine(conn_str, echo=False, connect_args={"timeout": 15})
        try:
            with test_eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            LoggerUtil.get_logger().error(
                f"Database.test_connection failed: {e}")
            return False

    def init_db(self) -> None: #For dev
        # """Import all models and create the tables if they do not exist."""
        # from backend.models.megawan_metronet import megawan_metronet_md
        # Base.metadata.create_all(bind=self.engine)

        pass