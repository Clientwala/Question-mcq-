"""
Configuration schemas for PDF processing.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ProcessingConfig(BaseModel):
    """
    Configuration for PDF processing.

    Used when creating a new job.
    """
    # PDF page range
    page_start: int = Field(ge=1, description="Starting page number (1-indexed)")
    page_end: int = Field(ge=1, description="Ending page number (1-indexed)")

    # Question range
    question_start: int = Field(ge=1, description="First question number")
    question_end: int = Field(ge=1, description="Last question number")

    # Optional metadata
    chapter_name: Optional[str] = Field(None, max_length=200, description="Chapter or section name")
    subject: Optional[str] = Field(None, max_length=100, description="Subject name")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Examination year")

    @field_validator('page_end')
    @classmethod
    def validate_page_range(cls, v, info):
        """Ensure page_end >= page_start."""
        if 'page_start' in info.data and v < info.data['page_start']:
            raise ValueError('page_end must be >= page_start')
        return v

    @field_validator('question_end')
    @classmethod
    def validate_question_range(cls, v, info):
        """Ensure question_end >= question_start."""
        if 'question_start' in info.data and v < info.data['question_start']:
            raise ValueError('question_end must be >= question_start')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "page_start": 44,
                "page_end": 64,
                "question_start": 101,
                "question_end": 150,
                "chapter_name": "Chapter 2 - Thermodynamics",
                "subject": "Physics",
                "year": 2023
            }
        }
    }
