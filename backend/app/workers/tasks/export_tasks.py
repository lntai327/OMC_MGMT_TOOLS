import asyncio
import json
import os
import uuid
from datetime import datetime
import redis
from app.core.config import settings
from app.core.database import get_worker_session
from app.core.logging import get_logger
from app.repositories.job_repo import job_repo
from app.services.module_registry import get_module_config
from app.workers.celery_app import celery

logger = get_logger("celery_worker.export")
_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL)
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            return None
    return _redis_client


def publish_progress_event(
    job_id: str,
    progress: int,
    status: str,
    meta: dict = None,
    error_message: str = None,
):
    try:
        r = get_redis_client()
        if r:
            event_payload = {
                "job_id": job_id,
                "progress": progress,
                "status": status,
                "result_meta": meta or {},
                "error_message": error_message,
            }
            r.publish(f"job:{job_id}", json.dumps(event_payload))
    except Exception as e:
        logger.warning(f"Failed to publish progress to Redis: {e}")


async def _run_export(job_id_str: str, filter_dict: dict, file_key: str):
    job_uuid = uuid.UUID(job_id_str)

    async with get_worker_session() as session:
        job = await job_repo.claim_next_pending_job(session, target_job_id=job_uuid)
        if not job:
            logger.warning(f"Could not claim export job {job_id_str}.")
            return
        publish_progress_event(job_id_str, 10, "processing")

    try:
        # 1. Lấy cấu hình phân hệ từ MODULE_REGISTRY
        module_cfg = get_module_config(file_key)
        repo = module_cfg["repo"]
        filter_schema_cls = module_cfg["filter_schema"]
        export_func = module_cfg["export_func"]
        template_name = module_cfg["template_name"]
        prefix = module_cfg["export_filename_prefix"]

        filters = filter_schema_cls(**filter_dict)

        # 2. Fetch data từ repository
        async with get_worker_session() as session:
            records_orm = await repo.get_all_by_filters_stream(session, filters)
            records = [r.to_dict() for r in records_orm]

        publish_progress_event(job_id_str, 40, "processing", {"fetched_rows": len(records)})

        # 3. Chuẩn bị đường dẫn xuất file
        time_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"{prefix}_{time_suffix}_{job_id_str[:8]}.xlsx"
        output_full_path = os.path.join(settings.EXPORTS_PATH, export_filename)
        template_full_path = os.path.join(settings.TEMPLATES_PATH, template_name)

        publish_progress_event(job_id_str, 70, "processing", {"writing_file": True})

        # 4. Stream ghi ra file Excel
        export_func(
            template_path=template_full_path,
            output_path=output_full_path,
            records=records
        )

        final_meta = {
            "total_rows": len(records),
            "filename": export_filename,
            "file_size": os.path.getsize(output_full_path),
        }

        # 5. Đánh dấu hoàn tất Job
        async with get_worker_session() as session:
            await job_repo.complete_job(
                session,
                job_uuid,
                output_file_path=output_full_path,
                result_meta=final_meta,
            )

        publish_progress_event(job_id_str, 100, "completed", final_meta)
        logger.info(f"Export Job {job_id_str} ({file_key}) completed. Exported {len(records)} rows to {export_filename}.")

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Export Job {job_id_str} ({file_key}) failed with error: {error_msg}")
        try:
            async with get_worker_session() as session:
                await job_repo.fail_job(session, job_uuid, error_msg)
        except Exception:
            pass
        publish_progress_event(
            job_id_str,
            0,
            "failed",
            meta={"error": error_msg},
            error_message=error_msg,
        )


@celery.task(name="app.workers.tasks.export_tasks.process_export")
def process_export(job_id: str, filter_dict: dict, file_key: str):
    """Generic Celery export task entrypoint."""
    asyncio.run(_run_export(job_id, filter_dict, file_key))
