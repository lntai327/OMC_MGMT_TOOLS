from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        result = await session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        result = await session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self, session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one() or 0

    async def create(self, session: AsyncSession, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        id: Any,
        obj_in: dict
    ) -> Optional[ModelType]:
        await session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
        )
        return await self.get(session, id)

    async def delete(self, session: AsyncSession, id: Any) -> bool:
        result = await session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0

