"""
MinIO/S3 storage utilities for file upload/download
"""
import logging
import uuid
from datetime import timedelta
from typing import Optional, Tuple
from django.conf import settings
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class MinIOStorage:
    """MinIO storage client for document uploads"""

    def __init__(self):
        """Initialize MinIO client"""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to create/check bucket: {e}")

    def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = 'application/octet-stream',
        folder: str = 'documents'
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Upload file to MinIO

        Args:
            file_data: File content as bytes
            filename: Original filename
            content_type: MIME type
            folder: Folder path in bucket

        Returns:
            Tuple of (storage_path, file_size) or (None, None) on error
        """
        try:
            # Generate unique filename
            file_id = uuid.uuid4()
            storage_path = f"{folder}/{file_id}/{filename}"

            # Upload file
            from io import BytesIO
            file_stream = BytesIO(file_data)
            file_size = len(file_data)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                data=file_stream,
                length=file_size,
                content_type=content_type
            )

            logger.info(f"Uploaded file to MinIO: {storage_path} ({file_size} bytes)")
            return storage_path, file_size

        except S3Error as e:
            logger.error(f"MinIO upload failed: {e}")
            return None, None

    def get_download_url(
        self,
        storage_path: str,
        expires: timedelta = timedelta(hours=1)
    ) -> Optional[str]:
        """
        Generate presigned download URL

        Args:
            storage_path: Path to file in bucket
            expires: URL expiration time (default 1 hour)

        Returns:
            Presigned URL or None on error
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                expires=expires
            )
            logger.info(f"Generated download URL for: {storage_path}")
            return url
        except S3Error as e:
            logger.error(f"Failed to generate download URL: {e}")
            return None

    def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from MinIO

        Args:
            storage_path: Path to file in bucket

        Returns:
            True if deleted, False on error
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=storage_path
            )
            logger.info(f"Deleted file from MinIO: {storage_path}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def file_exists(self, storage_path: str) -> bool:
        """
        Check if file exists in MinIO

        Args:
            storage_path: Path to file in bucket

        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=storage_path
            )
            return True
        except S3Error:
            return False


# Singleton instance
_minio_storage = None


def get_storage() -> MinIOStorage:
    """Get MinIO storage singleton instance"""
    global _minio_storage
    if _minio_storage is None:
        _minio_storage = MinIOStorage()
    return _minio_storage
