import asyncio
import logging
from app.core.database import get_worker_session
from app.repositories.job_repo import job_repo
from app.workers.celery_app import celery

logger = logging.getLogger("celery_worker.watchdog")


async def _check_and_fail_stalled():
    async with get_worker_session() as session:
        stalled_count = await job_repo.fail_stalled_jobs(session)
        if stalled_count > 0:
            logger.warning(f"Watchdog caught and marked {stalled_count} stalled tasks as FAILED.")
        else:
            logger.debug("Watchdog heartbeat: no stalled jobs detected.")
        return stalled_count


@celery.task(name="app.workers.watchdog.check_stalled_jobs")
def check_stalled_jobs():
    """Heartbeat monitor catching stalled jobs that exceeded timeout_at."""
    return asyncio.run(_check_and_fail_stalled())
