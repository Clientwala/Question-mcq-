"""
File Manager Service.

Handles file uploads, downloads, storage, and cleanup.
"""
import os
import shutil
import aiofiles
from pathlib import Path
from uuid import UUID
from typing import Optional
from fastapi import UploadFile
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """
    Manage file operations for PDF uploads and Word outputs.

    Storage structure:
    /data/
      uploads/
        {job-uuid}/
          input.pdf
      outputs/
        {job-uuid}/
          output.docx
    """

    def __init__(self):
        """Initialize file manager with storage paths."""
        self.base_path = Path(settings.STORAGE_PATH)
        self.uploads_path = self.base_path / 'uploads'
        self.outputs_path = self.base_path / 'outputs'

        # Create directories if they don't exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create storage directories if they don't exist."""
        self.uploads_path.mkdir(parents=True, exist_ok=True)
        self.outputs_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage paths initialized: {self.base_path}")

    async def save_upload(
        self,
        job_id: UUID,
        file: UploadFile,
        max_size_mb: Optional[int] = None
    ) -> str:
        """
        Save uploaded PDF file.

        Args:
            job_id: Job UUID
            file: FastAPI UploadFile object
            max_size_mb: Maximum file size in MB (from settings if not provided)

        Returns:
            Path to saved file

        Raises:
            ValueError: If file is too large or invalid
        """
        if max_size_mb is None:
            max_size_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)

        # Create job directory
        job_dir = self.uploads_path / str(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)

        # File path
        file_path = job_dir / 'input.pdf'

        # Save file in chunks (memory efficient for large files)
        total_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(chunk_size):
                    total_size += len(chunk)

                    # Check size limit
                    if total_size > max_size_mb * 1024 * 1024:
                        # Delete partial file
                        await f.close()
                        file_path.unlink(missing_ok=True)
                        raise ValueError(f"File too large: {total_size / (1024*1024):.2f}MB (max {max_size_mb}MB)")

                    await f.write(chunk)

            logger.info(f"Saved upload: {file_path} ({total_size / (1024*1024):.2f}MB)")
            return str(file_path)

        except Exception as e:
            # Cleanup on error
            file_path.unlink(missing_ok=True)
            logger.error(f"Error saving upload: {e}")
            raise

    def get_output_path(self, job_id: UUID, filename: str) -> str:
        """
        Get path for output file.

        Args:
            job_id: Job UUID
            filename: Output filename

        Returns:
            Full path for output file
        """
        job_dir = self.outputs_path / str(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)

        file_path = job_dir / filename
        return str(file_path)

    async def cleanup_job(self, job_id: UUID) -> bool:
        """
        Delete all files for a job.

        Args:
            job_id: Job UUID

        Returns:
            True if cleanup successful
        """
        try:
            # Delete uploads
            upload_dir = self.uploads_path / str(job_id)
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
                logger.info(f"Deleted upload directory: {upload_dir}")

            # Delete outputs
            output_dir = self.outputs_path / str(job_id)
            if output_dir.exists():
                shutil.rmtree(output_dir)
                logger.info(f"Deleted output directory: {output_dir}")

            return True

        except Exception as e:
            logger.error(f"Error cleaning up job {job_id}: {e}")
            return False

    def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes
        """
        return os.path.getsize(file_path) if os.path.exists(file_path) else 0

    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists.

        Args:
            file_path: Path to file

        Returns:
            True if file exists
        """
        return os.path.exists(file_path)

    async def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage info
        """
        def get_dir_size(path: Path) -> int:
            """Calculate total size of directory."""
            total = 0
            try:
                for item in path.rglob('*'):
                    if item.is_file():
                        total += item.stat().st_size
            except Exception as e:
                logger.error(f"Error calculating directory size: {e}")
            return total

        uploads_size = get_dir_size(self.uploads_path)
        outputs_size = get_dir_size(self.outputs_path)

        return {
            'uploads_size_mb': uploads_size / (1024 * 1024),
            'outputs_size_mb': outputs_size / (1024 * 1024),
            'total_size_mb': (uploads_size + outputs_size) / (1024 * 1024),
            'uploads_count': sum(1 for _ in self.uploads_path.glob('*')),
            'outputs_count': sum(1 for _ in self.outputs_path.glob('*')),
        }


# Global instance
file_manager = FileManager()
