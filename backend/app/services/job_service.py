import os
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.job import Job, JobType, JobStatus
from app.models.user import User
from app.repositories.job_repo import job_repo
from app.schemas.job import JobCreateResponse, JobStatusResponse
from app.workers.tasks.import_tasks import process_import
from app.workers.tasks.export_tasks import process_export
from app.core.timezone import isoformat_vietnam


class JobService:
    async def create_import_job(
        self,
        session: AsyncSession,
        user_id: int,
        temp_file_path: str,
        file_key: str,
    ) -> JobCreateResponse:
        job = await job_repo.create_job(
            session=session,
            user_id=user_id,
            job_type=JobType.IMPORT,
            input_file_path=temp_file_path,
        )
        await session.commit()

        # Enqueue background Celery task
        process_import.delay(str(job.id), temp_file_path, file_key)

        return JobCreateResponse(
            job_id=str(job.id),
            status=job.status.value if hasattr(job.status, "value") else str(job.status),
            message="Job accepted and queued for processing.",
        )

    async def create_export_job(
        self,
        session: AsyncSession,
        user_id: int,
        filter_dict: Dict[str, Any],
        file_key: str,
    ) -> JobCreateResponse:
        job = await job_repo.create_job(
            session=session,
            user_id=user_id,
            job_type=JobType.EXPORT,
            result_meta={
                "filters": filter_dict,
                "file_key": file_key,
            },
        )
        await session.commit()

        # Enqueue background Celery task
        process_export.delay(str(job.id), filter_dict, file_key)

        return JobCreateResponse(
            job_id=str(job.id),
            status=job.status.value if hasattr(job.status, "value") else str(job.status),
            message="Job accepted and queued for processing.",
        )

    async def get_job_status(
        self,
        session: AsyncSession,
        job_id: str,
        current_user: Optional[User] = None,
        base_download_url: str = "/api/v1/downloads",
    ) -> JobStatusResponse:
        try:
            job_uuid = uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format")

        job = await job_repo.get_by_uuid(session, job_uuid)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        # Multi-user data isolation: Non-admin can only check their own jobs
        if current_user and current_user.role != "admin" and job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this job",
            )

        # Always return a relative download path so the frontend can resolve it
        # against its own configured API base URL — avoids Docker-internal hostname leakage.
        download_url = None
        if job.status == JobStatus.COMPLETED and job.output_file_path:
            filename = os.path.basename(job.output_file_path)
            download_url = f"/api/v1/downloads/{filename}"

        return JobStatusResponse(
            job_id=str(job.id),
            status=job.status.value if hasattr(job.status, "value") else str(job.status),
            progress=job.progress,
            download_url=download_url,
            result_meta=job.result_meta,
            error_message=job.error_message,
            created_at=isoformat_vietnam(job.created_at) if job.created_at else None,
            updated_at=isoformat_vietnam(job.updated_at) if job.updated_at else None,
        )


job_service = JobService()

