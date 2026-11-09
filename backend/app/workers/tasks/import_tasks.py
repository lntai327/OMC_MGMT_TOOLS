import asyncio
import json
import uuid
import redis
from app.constant import constant as SC
from app.core.config import settings
from app.core.database import get_worker_session
from app.core.logging import get_logger
from app.repositories.job_repo import job_repo
from app.services.excel_streamer import ExcelStreamer
from app.services.module_registry import get_module_config
from app.workers.celery_app import celery

logger = get_logger("celery_worker.import", delay=False)
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
    """Publish real-time progress update to Redis for WebSocket distribution."""
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


async def _run_import(
    job_id_str: str,
    file_path: str,
    file_key: str,
):
    job_uuid = uuid.UUID(job_id_str)

    async with get_worker_session() as session:
        # 1. Claim job atomically using FOR UPDATE SKIP LOCKED
        job = await job_repo.claim_next_pending_job(session, target_job_id=job_uuid)
        if not job:
            logger.warning(f"Could not claim job {job_id_str} (already claimed or cancelled).")
            return

        publish_progress_event(job_id_str, 5, "processing")

    total_rows = 0
    inserted_rows = 0
    updated_rows = 0
    deleted_rows = 0
    failed_counter = 0

    try:
        # 2. Lấy repo tương ứng từ MODULE_REGISTRY
        module_cfg = get_module_config(file_key)
        repo = module_cfg["repo"]
        header_row_range = module_cfg["header_row_range"]

        logger.info(f"Bắt đầu xử lý import Job {job_id_str} với file_key '{file_key}'")

        # 3. Stream rows in chunks
        chunk_index = 0
        for chunk in ExcelStreamer.read_rows_chunked(
            file_path=file_path,
            file_key=file_key,
            chunk_size=500,
            header_row_range=header_row_range,
        ):
            async with get_worker_session() as session:
                logger.info(f"Job {job_id_str}: processing chunk {chunk_index} - {len(chunk)} rows")
                for row in chunk:
                    #
                    action_val = row.pop(SC.K_ACTION)
                    if action_val is None:
                        logger.warning(
                            f"Job {job_id_str}: {row.get(SC.K_ID)} no action."
                        )
                        failed_counter += 1
                        continue

                    try:
                        async with session.begin_nested():
                            match str(action_val).strip().lower():
                                case "delete":
                                    deleted = await repo.delete_by_id(session, row.get(SC.K_ID))
                                    if deleted:
                                        deleted_rows += 1
                                    else:
                                        logger.warning(
                                            f"Job {job_id_str}: delete failed — id={row.get(SC.K_ID)} không tồn tại."
                                        )
                                        failed_counter += 1
                                case "insert":
                                    # "insert" → upsert
                                    result = await repo.upsert_by_id(session, row)
                                    if result == "updated":
                                        updated_rows += 1
                                    else:
                                        inserted_rows += 1
                                case _:
                                    logger.warning(
                                        f"Job {job_id_str}: id={row.get(SC.K_ID)} unknown action '{action_val}'."
                                    )
                                    failed_counter += 1
                    except Exception as e:
                        logger.error(
                            f"Job {job_id_str}: lỗi xử lý row (action={action_val!r}): {e}"
                        )
                        failed_counter += 1

            total_rows += len(chunk)
            chunk_index += 1

            # Estimate progress (10% to 90%)
            progress = min(90, 10 + (chunk_index * 15))
            meta_info = {
                "failed_counter": failed_counter,
                "detail": (
                    f"Tổng bản ghi: {total_rows}\n"
                    f"Thành công: {inserted_rows + updated_rows + deleted_rows}\n"
                    f"Đã thêm: {inserted_rows}\n"
                    f"Cập nhật: {updated_rows}\n"
                    f"Đã xóa: {deleted_rows}"
                ),
            }

            async with get_worker_session() as session:
                await job_repo.update_progress(session, job_uuid, progress, meta_info)

            publish_progress_event(job_id_str, progress, "processing", meta_info)

        # 4. Mark complete
        final_meta = {
            "failed_counter": failed_counter,
            "detail": (
                f"Tổng bản ghi: {total_rows}\n"
                f"Thành công: {inserted_rows + updated_rows + deleted_rows}\n"
                f"Đã thêm: {inserted_rows}\n"
                f"Cập nhật: {updated_rows}\n"
                f"Đã xóa: {deleted_rows}"
            ),
        }
        async with get_worker_session() as session:
            await job_repo.complete_job(session, job_uuid, result_meta=final_meta)

        publish_progress_event(job_id_str, 100, "completed", final_meta)
        logger.info(
            f"Job {job_id_str} ({file_key}) hoàn tất. "
            f"Tổng: {total_rows} | Thêm: {inserted_rows} | Cập nhật: {updated_rows} "
            f"| Xóa: {deleted_rows} | Lỗi: {failed_counter}"
        )

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Job {job_id_str} ({file_key}) failed with error: {error_msg}")
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


@celery.task(name="app.workers.tasks.import_tasks.process_import")
def process_import(job_id: str, file_path: str, file_key: str):
    """Generic Celery task entrypoint for Excel imports."""
    asyncio.run(_run_import(job_id, file_path, file_key))
