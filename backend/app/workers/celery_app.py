import os
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery = Celery(
    "omc_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.import_tasks",
        "app.workers.tasks.export_tasks",
        "app.workers.tasks.cleanup_tasks",
        "app.workers.watchdog",
    ],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    # Periodic schedules via Celery Beat
    beat_schedule={
        "watchdog-stalled-jobs": {
            "task": "app.workers.watchdog.check_stalled_jobs",
            "schedule": 120.0,  # Run every 2 minutes
        },
        "cleanup-temporary-files": {
            "task": "app.workers.tasks.cleanup_tasks.purge_old_files",
            "schedule": 3600.0,  # Run every 1 hour
        },
    },
)

