"""
Job database model.
Tracks PDF processing jobs with status, progress, and results.
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class Job(Base):
    """
    Job model for tracking PDF processing tasks.

    Table: jobs
    """
    __tablename__ = "jobs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # File references
    pdf_filename = Column(String(500), nullable=False)
    pdf_path = Column(Text, nullable=False)
    output_filename = Column(String(500), nullable=True)
    output_path = Column(Text, nullable=True)

    # Configuration (stored as JSON)
    # Example: {page_start: 44, page_end: 64, question_start: 101, question_end: 150, chapter_name: "Chapter 2"}
    config = Column(JSONB, nullable=False)

    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True
    )  # pending, parsing, generating, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(200), nullable=True)  # "Parsing question 45/100"

    # Results
    total_questions = Column(Integer, nullable=True)
    diagrams_detected = Column(Integer, nullable=True)

    # Error information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)  # Stack trace, question number, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(hours=24),
        nullable=False,
        index=True
    )

    # Indexes
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_expires_at', 'expires_at'),
    )

    def __repr__(self):
        return f"<Job {self.id} - {self.status} ({self.progress}%)>"

    @property
    def is_expired(self) -> bool:
        """Check if job has expired (24 hours)."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_processing(self) -> bool:
        """Check if job is currently being processed."""
        return self.status in ['pending', 'parsing', 'generating']

    @property
    def is_complete(self) -> bool:
        """Check if job is completed successfully."""
        return self.status == 'completed'

    @property
    def has_failed(self) -> bool:
        """Check if job has failed."""
        return self.status == 'failed'
