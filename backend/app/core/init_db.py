import asyncio
import logging
from sqlalchemy import text
from app.core.config import settings
from app.core.database import db_manager
from app.models.base import Base
import app.models  # Ensure all model declarations (User, Job, MegawanMetronet, etc.) are loaded into Base.metadata
from app.core.seed import seed_default_admin

logger = logging.getLogger("init_db")


async def init_db(max_retries: int = 10, retry_delay: int = 2) -> None:
    """
    Ensures database connectivity, automatically creates all missing tables
    defined in SQLAlchemy models (Base.metadata.create_all), and seeds the initial default admin.
    Existing tables and columns will NOT be modified or dropped.
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Connecting to database (attempt {attempt}/{max_retries})...")
            async with db_manager.engine.begin() as conn:
                # 1. Connectivity check
                await conn.execute(text("SELECT 1"))

                # 2. Automatically create tables if they do not exist
                logger.info("Checking and creating missing database tables...")
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database schema checked/created successfully.")
            break
        except (OSError, Exception) as exc:
            if attempt == max_retries:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {exc}")
                raise
            logger.warning(
                f"Database not ready yet (attempt {attempt}/{max_retries}): {exc}. Retrying in {retry_delay}s..."
            )
            await asyncio.sleep(retry_delay)

    # 3. Seed default admin user
    await seed_default_admin()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
