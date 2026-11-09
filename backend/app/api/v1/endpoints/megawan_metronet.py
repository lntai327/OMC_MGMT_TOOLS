import os
import shutil
import uuid
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationParams
from app.schemas.job import JobCreateResponse
from app.schemas.megawan_metronet import (
    MegawanCreate,
    MegawanFilterParams,
    MegawanResponse,
    MegawanUpdate,
)
from app.services.job_service import job_service
from app.services.megawan_metronet_service import megawan_metronet_service
from app.constant import constant as SC

router = APIRouter(prefix="/megawan", tags=["Megawan & Metronet"])


@router.get("", response_model=PaginatedResponse[MegawanResponse])
async def list_megawan_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    sort_by: Optional[str] = None,
    sort_desc: bool = False,
    loai_hinh_tb: Optional[str] = None,
    ten_th_bao: Optional[str] = None,
    dia_chi: Optional[str] = None,
    loai_kenh: Optional[str] = None,
    svlan_cvlan: Optional[str] = None,
    ten_he_thong: Optional[str] = None,
    all_search: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = MegawanFilterParams(
        loai_hinh_tb=loai_hinh_tb,
        ten_th_bao=ten_th_bao,
        dia_chi=dia_chi,
        loai_kenh=loai_kenh,
        svlan_cvlan=svlan_cvlan,
        ten_he_thong=ten_he_thong,
        all_search=all_search,
    )
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    return await megawan_metronet_service.get_records(session, filters, pagination)


@router.get("/{record_id}", response_model=MegawanResponse)
async def get_megawan_record(
    record_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await megawan_metronet_service.get_by_id(session, record_id)


@router.post("", response_model=MegawanResponse, status_code=status.HTTP_201_CREATED)
async def create_megawan_record(
    data: MegawanCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "operator"])),
):
    return await megawan_metronet_service.create(session, data)


@router.put("/{record_id}", response_model=MegawanResponse)
async def update_megawan_record(
    record_id: int,
    data: MegawanUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "operator"])),
):
    return await megawan_metronet_service.update(session, record_id, data)


@router.delete("/{record_id}", response_model=MessageResponse)
async def delete_megawan_record(
    record_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    await megawan_metronet_service.delete(session, record_id)
    return MessageResponse(message=f"Record {record_id} deleted successfully.")


@router.post("/import", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def import_megawan_excel(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "operator"])),
):
    """Async Job endpoint accepting Excel upload and queuing Celery worker."""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Excel files (.xlsx, .xls) are allowed")

    os.makedirs(settings.UPLOADS_PATH, exist_ok=True)
    temp_filename = f"upload_{uuid.uuid4()}_{file.filename}"
    temp_file_path = os.path.join(settings.UPLOADS_PATH, temp_filename)

    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return await job_service.create_import_job(
        session=session,
        user_id=current_user.id,
        temp_file_path=temp_file_path,
        file_key=SC.K_EXCEL_MEGAWAN,
    )


@router.post("/export", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def export_megawan_excel(
    filters: MegawanFilterParams,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Async Job endpoint accepting filter criteria and queuing Celery export worker."""
    return await job_service.create_export_job(
        session=session,
        user_id=current_user.id,
        filter_dict=filters.model_dump(),
        file_key=SC.K_EXCEL_MEGAWAN,
    )

