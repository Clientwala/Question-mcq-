"""
Celery Application Configuration.

Background task processing for PDF parsing and document generation.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "pdf_question_generator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.processing",
        "app.tasks.cleanup"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Result backend
    result_expires=86400,  # 24 hours

    # Broker settings
    broker_connection_retry_on_startup=True,
)

# Celery Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    # Cleanup expired jobs every hour
    'cleanup-expired-jobs': {
        'task': 'app.tasks.cleanup.cleanup_expired_jobs',
        'schedule': crontab(minute=0),  # Every hour at minute 0
    },
}

# Task routes (optional - for multiple queues)
celery_app.conf.task_routes = {
    'app.tasks.processing.*': {'queue': 'processing'},
    'app.tasks.cleanup.*': {'queue': 'cleanup'},
}


if __name__ == "__main__":
    celery_app.start()
