import os
import time
import logging
from app.core.config import settings
from app.workers.celery_app import celery

logger = logging.getLogger("celery_worker.cleanup")


def _purge_directory_older_than(dir_path: str, max_age_seconds: int = 86400) -> int:
    if not os.path.exists(dir_path):
        return 0

    now = time.time()
    purged_count = 0

    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    purged_count += 1
                except Exception as e:
                    logger.warning(f"Could not remove old file {file_path}: {e}")

    return purged_count


@celery.task(name="app.workers.tasks.cleanup_tasks.purge_old_files")
def purge_old_files():
    """Purge temporary upload and export files older than 24 hours (86,400 seconds)."""
    max_age = 86400  # 24 hours
    purged_uploads = _purge_directory_older_than(settings.UPLOADS_PATH, max_age)
    purged_exports = _purge_directory_older_than(settings.EXPORTS_PATH, max_age)
    logger.info(f"File cleanup completed: purged {purged_uploads} uploads and {purged_exports} exports.")
    return {"purged_uploads": purged_uploads, "purged_exports": purged_exports}

