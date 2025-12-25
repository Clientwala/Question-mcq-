"""
PDF Processing Celery Task.

Background task that processes PDF, parses questions, and generates Word document.
"""
from celery import Task
from datetime import datetime
from app.core.celery_app import celery_app
from app.services.pdf_parser import PDFParser
from app.services.question_parser import QuestionParser
from app.services.document_generator import DocumentGenerator
from app.services.file_manager import file_manager
from app.services.websocket_manager import ws_manager
from app.db.base import SyncSessionLocal
from app.models.job import Job
from sqlalchemy import select
import logging
import asyncio

logger = logging.getLogger(__name__)


def send_progress_sync(job_id: str, progress: int, step: str):
    """Send progress update via WebSocket (synchronously)."""
    try:
        # Run async ws_manager in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            ws_manager.send_progress(job_id, {
                'progress': progress,
                'step': step,
                'timestamp': datetime.utcnow().isoformat()
            })
        )
        loop.close()
    except Exception as e:
        logger.error(f"Error sending progress: {e}")


@celery_app.task(bind=True)
def process_pdf_task(self, job_id: str):
    """
    Main PDF processing task with progress tracking.

    Steps:
    1. Extract PDF text (0-20%)
    2. Parse questions (20-70%)
    3. Generate document (70-95%)
    4. Save and finalize (95-100%)

    Args:
        self: Task instance (bound)
        job_id: Job UUID as string

    Raises:
        Exception: If processing fails
    """
    db = SyncSessionLocal()

    try:
        # Get job
        logger.info(f"Starting processing for job {job_id}")
        job = db.execute(
            select(Job).where(Job.id == job_id)
        ).scalar_one_or_none()

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        config = job.config

        # Update status to parsing
        job.status = 'parsing'
        job.started_at = datetime.utcnow()
        db.commit()

        # Step 1: Extract PDF text (0-20%)
        job.progress = 5
        job.current_step = "Extracting text from PDF..."
        db.commit()
        send_progress_sync(job_id, 5, "Extracting text from PDF...")

        pdf_parser = PDFParser()
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pdf_text = loop.run_until_complete(
            pdf_parser.extract_text(
                job.pdf_path,
                config['page_start'],
                config['page_end']
            )
        )
        loop.close()

        job.progress = 20
        job.current_step = "Text extracted successfully"
        db.commit()
        send_progress_sync(job_id, 20, "Text extracted successfully")

        # Step 2: Parse questions (20-70%)
        question_parser = QuestionParser()

        job.progress = 25
        job.current_step = "Starting question parsing..."
        db.commit()
        send_progress_sync(job_id, 25, "Starting question parsing...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        parsed_questions = loop.run_until_complete(
            question_parser.parse_questions(
                pdf_text,
                config['question_start'],
                config['question_end']
            )
        )
        loop.close()

        # Update progress for each question
        questions = []
        for i, question in enumerate(parsed_questions):
            questions.append(question)
            progress = 25 + int((i + 1) / len(parsed_questions) * 45)  # 25-70%
            job.progress = progress
            job.current_step = f"Parsing question {question.number}..."
            db.commit()
            send_progress_sync(job_id, progress, f"Parsing question {question.number}...")

        job.progress = 70
        job.current_step = f"Parsed {len(questions)} questions"
        db.commit()
        send_progress_sync(job_id, 70, f"Parsed {len(questions)} questions")

        # Step 3: Generate document (70-95%)
        job.status = 'generating'
        db.commit()

        job.progress = 75
        job.current_step = "Generating Word document..."
        db.commit()
        send_progress_sync(job_id, 75, "Generating Word document...")

        doc_gen = DocumentGenerator()

        # Generate filename
        filename = doc_gen.generate_filename(config)
        output_path = file_manager.get_output_path(job.id, filename)

        # Create document
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            doc_gen.create_document(
                questions,
                config,
                output_path
            )
        )
        loop.close()

        # Step 4: Finalize (95-100%)
        job.progress = 95
        job.current_step = "Finalizing document..."
        db.commit()
        send_progress_sync(job_id, 95, "Finalizing document...")

        # Update job
        job.status = 'completed'
        job.progress = 100
        job.current_step = "Complete!"
        job.output_path = output_path
        job.output_filename = filename
        job.total_questions = len(questions)
        job.diagrams_detected = sum(1 for q in questions if q.has_diagram)
        job.completed_at = datetime.utcnow()

        db.commit()

        send_progress_sync(job_id, 100, "Complete!")

        # Send completion event via WebSocket
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            ws_manager.send_complete(job_id, {
                'output_filename': filename,
                'total_questions': len(questions),
                'diagrams_detected': sum(1 for q in questions if q.has_diagram)
            })
        )
        loop.close()

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        # Handle errors
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)

        job = db.execute(
            select(Job).where(Job.id == job_id)
        ).scalar_one_or_none()

        if job:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

            # Send error event via WebSocket
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                ws_manager.send_error(job_id, str(e), {
                    'error_type': type(e).__name__
                })
            )
            loop.close()

        raise

    finally:
        db.close()
