from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.megawan_metronet import MegawanMetronet
from app.repositories.megawan_metronet_repo import megawan_metronet_repo
from app.schemas.megawan_metronet import (
    MegawanCreate,
    MegawanUpdate,
    MegawanFilterParams,
    MegawanResponse,
)
from app.schemas.common import PaginationParams, PaginatedResponse


class MegawanMetronetService:
    async def get_records(
        self,
        session: AsyncSession,
        filters: MegawanFilterParams,
        pagination: PaginationParams,
    ) -> PaginatedResponse[MegawanResponse]:
        skip = (pagination.page - 1) * pagination.page_size
        items, total = await megawan_metronet_repo.get_filtered_records(
            session=session,
            filters=filters,
            skip=skip,
            limit=pagination.page_size,
            sort_by=pagination.sort_by,
            sort_desc=pagination.sort_desc,
        )

        total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0

        return PaginatedResponse(
            items=[MegawanResponse.model_validate(item) for item in items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
        )

    async def get_by_id(self, session: AsyncSession, record_id: int) -> MegawanResponse:
        record = await megawan_metronet_repo.get(session, record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        return MegawanResponse.model_validate(record)

    async def create(self, session: AsyncSession, data: MegawanCreate) -> MegawanResponse:
        record_dict = data.model_dump(exclude_unset=True)
        record_dict["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        created = await megawan_metronet_repo.create(session, record_dict)
        return MegawanResponse.model_validate(created)

    async def update(self, session: AsyncSession, record_id: int, data: MegawanUpdate) -> MegawanResponse:
        record = await megawan_metronet_repo.get(session, record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

        record_dict = data.model_dump(exclude_unset=True)
        record_dict["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        updated = await megawan_metronet_repo.update(session, record_id, record_dict)
        return MegawanResponse.model_validate(updated)

    async def delete(self, session: AsyncSession, record_id: int) -> bool:
        record = await megawan_metronet_repo.get(session, record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

        return await megawan_metronet_repo.delete(session, record_id)


megawan_metronet_service = MegawanMetronetService()

