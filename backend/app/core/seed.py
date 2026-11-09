import asyncio
import logging
from app.core.config import settings
from app.core.database import db_manager
from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repo import user_repo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


async def seed_default_admin():
    async with db_manager.session_factory() as session:
        existing = await user_repo.get_by_username(session, settings.FIRST_SUPERUSER_USERNAME)
        if not existing:
            admin_user = User(
                username=settings.FIRST_SUPERUSER_USERNAME,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                role="admin",
                is_active=True,
            )
            session.add(admin_user)
            await session.commit()
            logger.info(f"Default admin user '{settings.FIRST_SUPERUSER_USERNAME}' created successfully.")
        else:
            logger.info(f"Admin user '{settings.FIRST_SUPERUSER_USERNAME}' already exists.")


if __name__ == "__main__":
    asyncio.run(seed_default_admin())

