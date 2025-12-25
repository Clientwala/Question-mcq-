"""
Cleanup Celery Task.

Periodic task to cleanup expired jobs (24-hour retention).
"""
from celery import Task
from datetime import datetime
from app.core.celery_app import celery_app
from app.services.file_manager import file_manager
from app.db.base import AsyncSessionLocal
from app.models.job import Job
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


@celery_app.task
def cleanup_expired_jobs():
    """
    Periodic task to cleanup jobs older than 24 hours.

    Runs: Every hour (configured in Celery beat)

    Actions:
    1. Find jobs where expires_at < NOW()
    2. Delete PDF files
    3. Delete Word document files
    4. Delete database records
    """
    import asyncio

    async def cleanup():
        """Async cleanup function."""
        async with AsyncSessionLocal() as db:
            try:
                # Find expired jobs
                result = await db.execute(
                    select(Job).where(
                        Job.expires_at < datetime.utcnow(),
                        Job.status.in_(['completed', 'failed'])
                    )
                )
                expired_jobs = result.scalars().all()

                if not expired_jobs:
                    logger.info("No expired jobs to cleanup")
                    return {
                        'cleaned': 0,
                        'failed': 0,
                        'timestamp': datetime.utcnow().isoformat()
                    }

                logger.info(f"Found {len(expired_jobs)} expired jobs to cleanup")

                cleaned_count = 0
                failed_count = 0

                for job in expired_jobs:
                    try:
                        # Delete files
                        success = await file_manager.cleanup_job(job.id)

                        if success:
                            # Delete database record
                            await db.delete(job)
                            cleaned_count += 1
                            logger.info(f"Cleaned up job {job.id}")
                        else:
                            failed_count += 1
                            logger.warning(f"Failed to cleanup files for job {job.id}")

                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Error cleaning job {job.id}: {e}")

                # Commit deletions
                await db.commit()

                result = {
                    'cleaned': cleaned_count,
                    'failed': failed_count,
                    'timestamp': datetime.utcnow().isoformat()
                }

                logger.info(f"Cleanup complete: {result}")
                return result

            except Exception as e:
                logger.error(f"Cleanup task failed: {e}", exc_info=True)
                raise

    # Run async function
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(cleanup())
