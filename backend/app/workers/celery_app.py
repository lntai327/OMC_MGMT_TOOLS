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
    # Chống overload RAM & CPU:
    # 1. Chỉ nhận 1 task tại một thời điểm cho mỗi slot, không gom trước task nặng vào bộ nhớ
    worker_prefetch_multiplier=1,
    # 2. Chỉ xác nhận (ACK) khi task đã xử lý xong để tránh mất task khi worker crash
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # 3. Giới hạn thời gian tối đa tránh treo tiến trình vĩnh viễn (9 phút cảnh báo mềm, 10 phút ngắt cưỡng bức)
    task_soft_time_limit=540,
    task_time_limit=600,
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

