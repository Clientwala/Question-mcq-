"""
Document Generator Service.

Generates formatted Word documents from parsed questions.
Uses formatting utilities ported from existing scripts.
"""
from docx import Document
from docx.shared import Cm
from typing import List, Optional, Callable
from app.services.question_parser import ParsedQuestion
from app.utils.formatters import add_question_table
import logging

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """
    Generate Word documents from parsed questions.

    Uses exact formatting from existing scripts:
    - Font: Times New Roman, 14pt, Bold
    - Table: 8 rows × 3 columns
    - Page margins: 3.5cm top, 2.4cm others
    - Column widths: 1.5cm, 8.5cm, 3.0cm
    """

    # Formatting constants
    FONT_NAME = 'Times New Roman'
    FONT_SIZE = 14  # points
    FONT_BOLD = True

    # Page margins (in cm)
    MARGIN_TOP = 3.5
    MARGIN_BOTTOM = 2.4
    MARGIN_LEFT = 2.4
    MARGIN_RIGHT = 2.4

    # Column widths (in cm)
    COL_WIDTH_LABEL = 1.5
    COL_WIDTH_CONTENT = 8.5
    COL_WIDTH_STATUS = 3.0

    async def create_document(
        self,
        questions: List[ParsedQuestion],
        config: dict,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """
        Create Word document from parsed questions.

        Args:
            questions: List of ParsedQuestion objects
            config: Processing configuration (for filename, metadata)
            output_path: Path where to save the document
            progress_callback: Optional callback for progress updates (0.0-1.0)

        Returns:
            Path to generated document

        Raises:
            Exception: If document generation fails
        """
        try:
            logger.info(f"Generating document with {len(questions)} questions")

            # Create new document
            doc = Document()

            # Set page margins
            self._set_page_margins(doc)

            # Add each question as a table
            total_questions = len(questions)

            for idx, question in enumerate(questions):
                logger.debug(f"Adding question {question.number} ({idx + 1}/{total_questions})")

                # Add question table
                self._add_question(doc, question)

                # Add page break (except for last question)
                if idx < total_questions - 1:
                    doc.add_page_break()

                # Progress callback
                if progress_callback:
                    progress = (idx + 1) / total_questions
                    progress_callback(progress)

            # Save document
            doc.save(output_path)
            logger.info(f"Document saved to: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error generating document: {e}", exc_info=True)
            raise Exception(f"Failed to generate document: {str(e)}")

    def _set_page_margins(self, doc):
        """Set page margins for document."""
        for section in doc.sections:
            section.top_margin = Cm(self.MARGIN_TOP)
            section.bottom_margin = Cm(self.MARGIN_BOTTOM)
            section.left_margin = Cm(self.MARGIN_LEFT)
            section.right_margin = Cm(self.MARGIN_RIGHT)

    def _add_question(self, doc, question: ParsedQuestion):
        """
        Add a single question to document.

        Args:
            doc: Document object
            question: ParsedQuestion object
        """
        # Use the formatting utility to add question table
        add_question_table(
            doc,
            question_parts=question.question_text,
            options=question.options,
            correct_option_idx=question.correct_option_idx,
            solution_parts=question.solution_text,
            has_diagram=question.has_diagram
        )

    async def validate_questions(self, questions: List[ParsedQuestion]) -> bool:
        """
        Validate questions before generating document.

        Checks:
        - All questions have 4 options
        - Correct option index is valid (0-3)
        - Required fields are present

        Args:
            questions: List of ParsedQuestion objects

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        for q in questions:
            # Check options count
            if len(q.options) != 4:
                raise ValueError(f"Question {q.number}: Expected 4 options, found {len(q.options)}")

            # Check correct option index
            if not (0 <= q.correct_option_idx < 4):
                raise ValueError(f"Question {q.number}: Invalid correct option index {q.correct_option_idx}")

            # Check required fields
            if not q.question_text:
                raise ValueError(f"Question {q.number}: Missing question text")

            if not q.solution_text:
                logger.warning(f"Question {q.number}: Missing solution text")

        return True

    def generate_filename(self, config: dict) -> str:
        """
        Generate output filename from config.

        Format: {chapter_name}_Q{start}-{end}.docx
        Example: Chapter2_Thermodynamics_Q101-150.docx

        Args:
            config: Processing configuration

        Returns:
            Generated filename
        """
        chapter = config.get('chapter_name', 'Questions')
        q_start = config.get('question_start', 1)
        q_end = config.get('question_end', 100)

        # Clean chapter name (remove special characters)
        chapter_clean = ''.join(c for c in chapter if c.isalnum() or c in [' ', '_', '-'])
        chapter_clean = chapter_clean.replace(' ', '_')

        filename = f"{chapter_clean}_Q{q_start}-{q_end}.docx"
        return filename

    async def get_document_stats(self, questions: List[ParsedQuestion]) -> dict:
        """
        Get statistics about the document.

        Args:
            questions: List of ParsedQuestion objects

        Returns:
            Dictionary with stats
        """
        return {
            'total_questions': len(questions),
            'diagrams_detected': sum(1 for q in questions if q.has_diagram),
            'low_confidence_count': sum(1 for q in questions if q.confidence < 0.7),
            'average_confidence': sum(q.confidence for q in questions) / len(questions) if questions else 0,
            'question_numbers': [q.number for q in questions],
        }
