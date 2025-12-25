"""
Job schemas for API requests and responses.
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID


class JobBase(BaseModel):
    """Base job schema with common fields."""
    pdf_filename: str
    status: str
    progress: int
    current_step: Optional[str] = None


class JobCreate(BaseModel):
    """Schema for creating a new job (internal use)."""
    pdf_filename: str
    pdf_path: str
    config: dict


class JobResponse(BaseModel):
    """
    Job status response schema.

    Returned by API endpoints.
    """
    # Identification
    id: UUID
    pdf_filename: str

    # Status
    status: str  # pending, parsing, generating, completed, failed
    progress: int  # 0-100
    current_step: Optional[str] = None

    # Results (when completed)
    output_filename: Optional[str] = None
    total_questions: Optional[int] = None
    diagrams_detected: Optional[int] = None

    # Error (when failed)
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: datetime

    # Config from model
    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """Response schema for listing jobs."""
    jobs: list[JobResponse]
    total: int


class JobProgressUpdate(BaseModel):
    """Real-time progress update via WebSocket."""
    progress: int
    step: str
    timestamp: datetime


class JobCompleteEvent(BaseModel):
    """Job completion event via WebSocket."""
    output_filename: str
    total_questions: int
    diagrams_detected: int


class JobErrorEvent(BaseModel):
    """Job error event via WebSocket."""
    message: str
    details: Optional[dict] = None
