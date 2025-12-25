"""
PDF Parser Service.

Extracts text from PDF files using pdfplumber.
"""
import pdfplumber
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PDFParser:
    """
    PDF text extraction service using pdfplumber.

    pdfplumber is preferred over pypdf2 because:
    - Better text extraction quality
    - Layout-aware (preserves positioning)
    - Table detection capabilities
    - No external dependencies (pure Python)
    """

    @staticmethod
    async def extract_text(
        pdf_path: str,
        start_page: int,
        end_page: int
    ) -> str:
        """
        Extract text from specified PDF page range.

        Args:
            pdf_path: Path to PDF file
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed)

        Returns:
            Extracted text as string

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If page range is invalid
            Exception: For other PDF reading errors
        """
        try:
            logger.info(f"Opening PDF: {pdf_path}")
            logger.info(f"Extracting pages {start_page} to {end_page}")

            text_content = []

            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"PDF has {total_pages} pages")

                # Validate page range
                if start_page < 1:
                    raise ValueError("start_page must be >= 1")
                if end_page > total_pages:
                    raise ValueError(f"end_page ({end_page}) exceeds total pages ({total_pages})")
                if start_page > end_page:
                    raise ValueError(f"start_page ({start_page}) must be <= end_page ({end_page})")

                # Extract text from specified pages
                for page_num in range(start_page - 1, end_page):
                    page = pdf.pages[page_num]
                    text = page.extract_text()

                    if text:
                        text_content.append(text)
                        logger.debug(f"Extracted {len(text)} characters from page {page_num + 1}")
                    else:
                        logger.warning(f"No text found on page {page_num + 1}")

            # Join all page text with double newlines
            full_text = "\n\n".join(text_content)
            logger.info(f"Total text extracted: {len(full_text)} characters")

            return full_text

        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except ValueError as e:
            logger.error(f"Invalid page range: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}", exc_info=True)
            raise Exception(f"Failed to extract PDF text: {str(e)}")

    @staticmethod
    async def get_pdf_info(pdf_path: str) -> dict:
        """
        Get PDF metadata and information.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with PDF info: {total_pages, metadata}
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return {
                    "total_pages": len(pdf.pages),
                    "metadata": pdf.metadata,
                }
        except Exception as e:
            logger.error(f"Error getting PDF info: {e}")
            raise

    @staticmethod
    async def validate_pdf(pdf_path: str, max_size_mb: int = 50) -> bool:
        """
        Validate PDF file.

        Args:
            pdf_path: Path to PDF file
            max_size_mb: Maximum allowed file size in MB

        Returns:
            True if valid, raises exception otherwise

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large or not a valid PDF
        """
        import os

        # Check file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"File not found: {pdf_path}")

        # Check file size
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValueError(f"File too large: {file_size_mb:.2f}MB (max {max_size_mb}MB)")

        # Try to open as PDF
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    raise ValueError("PDF has no pages")
        except Exception as e:
            raise ValueError(f"Invalid PDF file: {str(e)}")

        return True
