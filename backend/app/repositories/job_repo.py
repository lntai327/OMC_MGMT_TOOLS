import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job, JobStatus, JobType
from app.repositories.base_repo import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self):
        super().__init__(Job)

    async def get_by_uuid(self, session: AsyncSession, job_id: uuid.UUID) -> Optional[Job]:
        result = await session.execute(
            select(Job).where(Job.id == job_id)
        )
        return result.scalars().first()

    async def create_job(
        self,
        session: AsyncSession,
        user_id: int,
        job_type: JobType,
        input_file_path: Optional[str] = None,
        output_file_path: Optional[str] = None,
        result_meta: Optional[Dict[str, Any]] = None,
    ) -> Job:
        job = Job(
            id=uuid.uuid4(),
            user_id=user_id,
            type=job_type,
            status=JobStatus.PENDING,
            progress=0,
            input_file_path=input_file_path,
            output_file_path=output_file_path,
            result_meta=result_meta or {},
        )
        session.add(job)
        await session.flush()
        await session.refresh(job)
        return job

    async def claim_next_pending_job(
        self,
        session: AsyncSession,
        timeout_minutes: int = 15,
        target_job_id: Optional[uuid.UUID] = None,
    ) -> Optional[Job]:
        """Atomically claim a pending task using PostgreSQL FOR UPDATE SKIP LOCKED.
        If target_job_id is provided, tries to claim that specific job safely.
        """
        now = datetime.now(timezone.utc)
        timeout_at = now + timedelta(minutes=timeout_minutes)

        if target_job_id:
            # Lock the specific job
            query = (
                select(Job)
                .where(Job.id == target_job_id, Job.status == JobStatus.PENDING)
                .with_for_update(skip_locked=True)
            )
        else:
            query = (
                select(Job)
                .where(Job.status == JobStatus.PENDING)
                .order_by(Job.created_at.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
            )

        result = await session.execute(query)
        job = result.scalars().first()

        if job:
            job.status = JobStatus.PROCESSING
            job.timeout_at = timeout_at
            job.updated_at = now
            await session.flush()
            await session.refresh(job)
            return job

        return None

    async def update_progress(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        progress: int,
        meta_updates: Optional[Dict[str, Any]] = None
    ) -> None:
        values = {"progress": progress, "updated_at": datetime.now(timezone.utc)}
        if meta_updates:
            job = await self.get_by_uuid(session, job_id)
            if job and job.result_meta:
                merged = dict(job.result_meta)
                merged.update(meta_updates)
                values["result_meta"] = merged
            elif job:
                values["result_meta"] = meta_updates

        await session.execute(
            update(Job).where(Job.id == job_id).values(**values)
        )

    async def complete_job(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        output_file_path: Optional[str] = None,
        result_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        values = {
            "status": JobStatus.COMPLETED,
            "progress": 100,
            "updated_at": datetime.now(timezone.utc),
        }
        if output_file_path:
            values["output_file_path"] = output_file_path
        if result_meta:
            values["result_meta"] = result_meta

        await session.execute(
            update(Job).where(Job.id == job_id).values(**values)
        )

    async def fail_job(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        error_message: str,
    ) -> None:
        await session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                status=JobStatus.FAILED,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
        )

    async def fail_stalled_jobs(self, session: AsyncSession) -> int:
        """Finds all processing tasks that exceeded their timeout_at and marks them failed."""
        now = datetime.now(timezone.utc)
        result = await session.execute(
            update(Job)
            .where(
                Job.status == JobStatus.PROCESSING,
                Job.timeout_at < now,
            )
            .values(
                status=JobStatus.FAILED,
                error_message="Task timeout exceeded",
                updated_at=now,
            )
        )
        return result.rowcount or 0


job_repo = JobRepository()

