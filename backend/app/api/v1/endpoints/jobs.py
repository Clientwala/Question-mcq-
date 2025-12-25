"""
Jobs API Endpoints.

Handles job creation, status retrieval, and file downloads.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import uuid
import logging

from app.api.deps import get_db
from app.models.job import Job
from app.schemas.job import JobResponse, JobListResponse
from app.schemas.config import ProcessingConfig
from app.services.file_manager import file_manager
from app.tasks.processing import process_pdf_task
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse, status_code=201)
async def create_job(
    pdf_file: UploadFile = File(..., description="PDF file to process"),
    page_start: int = Form(..., ge=1, description="Starting page number"),
    page_end: int = Form(..., ge=1, description="Ending page number"),
    question_start: int = Form(..., ge=1, description="First question number"),
    question_end: int = Form(..., ge=1, description="Last question number"),
    chapter_name: Optional[str] = Form(None, max_length=200, description="Chapter name"),
    subject: Optional[str] = Form(None, max_length=100, description="Subject"),
    year: Optional[int] = Form(None, ge=1900, le=2100, description="Year"),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new PDF processing job.

    Steps:
    1. Validate PDF file
    2. Save to storage
    3. Create job record in database
    4. Queue Celery task for processing
    5. Return job ID and initial status

    Args:
        pdf_file: Uploaded PDF file
        page_start: Starting page number (1-indexed)
        page_end: Ending page number (1-indexed)
        question_start: First question number to extract
        question_end: Last question number to extract
        chapter_name: Optional chapter/section name
        subject: Optional subject name
        year: Optional examination year
        db: Database session

    Returns:
        JobResponse with job details

    Raises:
        HTTPException 400: Invalid file or parameters
        HTTPException 413: File too large
    """
    logger.info(f"Creating job for PDF: {pdf_file.filename}")

    # Validate file extension
    if not pdf_file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Validate page range
    if page_end < page_start:
        raise HTTPException(
            status_code=400,
            detail=f"page_end ({page_end}) must be >= page_start ({page_start})"
        )

    # Validate question range
    if question_end < question_start:
        raise HTTPException(
            status_code=400,
            detail=f"question_end ({question_end}) must be >= question_start ({question_start})"
        )

    try:
        # Generate job ID
        job_id = uuid.uuid4()
        logger.info(f"Generated job ID: {job_id}")

        # Save PDF file
        pdf_path = await file_manager.save_upload(job_id, pdf_file)
        logger.info(f"Saved PDF to: {pdf_path}")

        # Create configuration
        config = {
            "page_start": page_start,
            "page_end": page_end,
            "question_start": question_start,
            "question_end": question_end,
            "chapter_name": chapter_name,
            "subject": subject,
            "year": year
        }

        # Create job record
        job = Job(
            id=job_id,
            pdf_filename=pdf_file.filename,
            pdf_path=pdf_path,
            config=config,
            status="pending",
            progress=0
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info(f"Created job record: {job_id}")

        # Queue Celery task
        process_pdf_task.delay(str(job_id))
        logger.info(f"Queued processing task for job: {job_id}")

        return JobResponse.model_validate(job)

    except ValueError as e:
        # File validation errors
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Cleanup on error
        logger.error(f"Error creating job: {e}", exc_info=True)
        if 'job_id' in locals():
            await file_manager.cleanup_job(job_id)
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get job status and details.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        JobResponse with current job status

    Raises:
        HTTPException 404: Job not found
    """
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    return JobResponse.model_validate(job)


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List recent jobs (last 24 hours).

    Args:
        limit: Maximum number of jobs to return (default 20, max 100)
        offset: Number of jobs to skip (for pagination)
        status: Optional status filter (pending, parsing, generating, completed, failed)
        db: Database session

    Returns:
        JobListResponse with list of jobs

    Raises:
        HTTPException 400: Invalid parameters
    """
    # Validate limit
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 20

    # Cutoff: last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)

    # Build query
    query = select(Job).where(Job.created_at >= cutoff)

    # Filter by status if provided
    if status:
        valid_statuses = ['pending', 'parsing', 'generating', 'completed', 'failed']
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        query = query.where(Job.status == status)

    # Order by creation time (newest first)
    query = query.order_by(desc(Job.created_at))

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    jobs = result.scalars().all()

    # Get total count
    count_query = select(Job).where(Job.created_at >= cutoff)
    if status:
        count_query = count_query.where(Job.status == status)

    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total
    )


@router.get("/{job_id}/download")
async def download_result(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Download generated Word document.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        FileResponse with Word document

    Raises:
        HTTPException 404: Job not found or not completed
        HTTPException 410: Job expired (files deleted)
    """
    # Get job
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    # Check if job is completed
    if job.status != 'completed':
        raise HTTPException(
            status_code=404,
            detail=f"Job not completed yet (status: {job.status})"
        )

    # Check if output file exists
    if not job.output_path or not file_manager.file_exists(job.output_path):
        # Check if expired
        if job.is_expired:
            raise HTTPException(
                status_code=410,
                detail="Job expired - files have been deleted after 24 hours"
            )
        raise HTTPException(
            status_code=404,
            detail="Output file not found"
        )

    # Return file
    return FileResponse(
        path=job.output_path,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename=job.output_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{job.output_filename}"'
        }
    )


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a job and its files.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        204 No Content

    Raises:
        HTTPException 404: Job not found
        HTTPException 409: Cannot delete job that is still processing
    """
    # Get job
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    # Don't allow deleting jobs that are still processing
    if job.is_processing:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete job that is still processing"
        )

    # Delete files
    await file_manager.cleanup_job(job_id)

    # Delete database record
    await db.delete(job)
    await db.commit()

    logger.info(f"Deleted job: {job_id}")
