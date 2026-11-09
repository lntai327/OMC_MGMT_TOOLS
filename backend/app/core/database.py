from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from app.core.config import settings


class DatabaseManager:
    """Database abstraction manager supporting PostgreSQL and MSSQL dialects."""

    def __init__(self, db_url: str = settings.DATABASE_URL):
        self.db_url = db_url
        self.engine: AsyncEngine = self._create_engine(db_url)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def _create_engine(self, db_url: str) -> AsyncEngine:
        connect_args = {}
        # If connecting to PostgreSQL asyncpg
        if "postgresql" in db_url:
            connect_args = {
                "server_settings": {
                    "application_name": "omc_report_tools"
                }
            }
        # If connecting to MSSQL via aioodbc / async driver
        elif "mssql" in db_url:
            connect_args = {"timeout": 30}

        return create_async_engine(
            db_url,
            echo=settings.DB_ECHO,
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            connect_args=connect_args,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def check_health(self) -> bool:
        """Ping database to verify connectivity."""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def close(self):
        await self.engine.dispose()


# Global DB instance
db_manager = DatabaseManager()


from contextlib import asynccontextmanager
from sqlalchemy.pool import NullPool


@asynccontextmanager
async def get_worker_session():
    """Provides an isolated async session for Celery workers with NullPool to prevent event-loop conflicts."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for accessing database sessions."""
    async with db_manager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

