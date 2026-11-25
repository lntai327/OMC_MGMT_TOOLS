import asyncio
import json
import uuid
from typing import Any, Dict
import redis
from sqlalchemy import inspect
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


def _truncate_row_fields(
    row: Dict[str, Any],
    col_max_lengths: Dict[str, int],
    job_id_str: str,
    row_identifier: Any = None,
) -> Dict[str, Any]:
    """Kiểm tra độ dài thực tế của các column trong table DB, so sánh với độ dài input,

    cắt bớt input nếu vượt quá và ghi log cảnh báo.
    """
    for field_name, field_val in list(row.items()):
        if field_val is not None and field_name in col_max_lengths:
            max_len = col_max_lengths[field_name]
            str_val = str(field_val)
            if len(str_val) > max_len:
                logger.warning(
                    f"Job {job_id_str}: Row id={row_identifier!r}, cột '{field_name}' có độ dài {len(str_val)} "
                    f"vượt quá giới hạn cột DB ({max_len}). Đã cắt bớt còn {max_len} ký tự."
                )
                row[field_name] = str_val[:max_len]
    return row


async def _get_column_max_lengths(session: Any, repo: Any) -> Dict[str, int]:
    """Lấy giới hạn độ dài thực tế của các cột từ table DB và Model."""
    col_limits: Dict[str, int] = {}

    # 1. Lấy từ Model definition trước
    model = getattr(repo, "model", None)
    if model and hasattr(model, "__table__"):
        for col in model.__table__.columns:
            length = getattr(col.type, "length", None)
            if length is not None and isinstance(length, int):
                col_limits[col.name] = length

    # 2. Truy vấn trực tiếp schema metadata thực tế từ DB để đảm bảo đồng bộ
    table_name = getattr(model, "__tablename__", None)
    if table_name and session:
        try:
            def _inspect_db(sync_session):
                insp = inspect(sync_session.connection())
                db_cols = insp.get_columns(table_name)
                limits = {}
                for col in db_cols:
                    col_name = col.get("name")
                    col_type = col.get("type")
                    length = getattr(col_type, "length", None)
                    if length is not None and isinstance(length, int):
                        limits[col_name] = length
                return limits

            db_limits = await session.run_sync(_inspect_db)
            if db_limits:
                col_limits.update(db_limits)
        except Exception as e:
            logger.warning(
                f"Không thể kiểm tra độ dài cột trực tiếp từ DB cho bảng '{table_name}': {e}. "
                f"Sẽ sử dụng giới hạn từ Model definition."
            )

    return col_limits


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

        # 2.1. Lấy độ dài thực tế của các column trong table DB
        col_max_lengths: Dict[str, int] = {}
        try:
            async with get_worker_session() as session:
                col_max_lengths = await _get_column_max_lengths(session, repo)
            if col_max_lengths:
                table_name = getattr(getattr(repo, "model", None), "__tablename__", "unknown")
                logger.info(
                    f"Job {job_id_str}: Đã nạp giới hạn độ dài các cột cho bảng '{table_name}': {col_max_lengths}"
                )
        except Exception as e:
            logger.warning(f"Job {job_id_str}: Lỗi khi lấy schema cột DB: {e}")

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
                    row_id = row.get(SC.K_ID)
                    action_val = row.pop(SC.K_ACTION, None)
                    if action_val is None or not str(action_val).strip():
                        logger.warning(
                            f"Job {job_id_str}: id={row_id} no action."
                        )
                        failed_counter += 1
                        continue

                    # Kiểm tra và cắt bớt input nếu độ dài vượt quá giới hạn column trong DB
                    if col_max_lengths:
                        _truncate_row_fields(row, col_max_lengths, job_id_str, row_identifier=row_id)

                    try:
                        async with session.begin_nested():
                            match str(action_val).strip().lower():
                                case "delete":
                                    deleted = await repo.delete_by_id(session, row_id)
                                    if deleted:
                                        deleted_rows += 1
                                    else:
                                        logger.warning(
                                            f"Job {job_id_str}: delete failed — id={row_id} không tồn tại."
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
                                        f"Job {job_id_str}: id={row_id} unknown action '{action_val}'."
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
