from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.job import JobType, JobStatus


class JobCreateResponse(BaseModel):
    job_id: str
    status: str = "pending"
    message: str = "Job accepted and queued for processing."


class JobResultMeta(BaseModel):
    failed_counter: Optional[int] = None
    detail: Optional[Dict[str, Any]] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int = Field(default=0, ge=0, le=100)
    download_url: Optional[str] = None
    result_meta: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class JobCreateRequest(BaseModel):
    type: JobType
    meta_params: Optional[Dict[str, Any]] = None

