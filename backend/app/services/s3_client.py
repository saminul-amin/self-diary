"""
S3/Minio client wrapper for file storage operations.

Provides upload, download URL generation, and delete via boto3.
"""

import logging
import uuid

import boto3

from app.config import settings

logger = logging.getLogger(__name__)


def _get_s3_client():
    """Create a boto3 S3 client configured for the current environment."""
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )


def generate_storage_key(user_id: uuid.UUID, entry_id: uuid.UUID, file_name: str) -> str:
    """Generate a unique S3 object key."""
    unique = uuid.uuid4().hex[:8]
    return f"{user_id}/{entry_id}/{unique}_{file_name}"


def upload_file(storage_key: str, file_data: bytes, content_type: str) -> None:
    """Upload a file to S3/Minio."""
    client = _get_s3_client()
    client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=storage_key,
        Body=file_data,
        ContentType=content_type,
    )
    logger.info("Uploaded file to S3: %s", storage_key)


def generate_presigned_url(storage_key: str, expires_in: int = 3600) -> str:
    """Generate a pre-signed download URL for an S3 object."""
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": storage_key},
        ExpiresIn=expires_in,
    )


def delete_file(storage_key: str) -> None:
    """Delete a file from S3/Minio."""
    client = _get_s3_client()
    client.delete_object(
        Bucket=settings.s3_bucket_name,
        Key=storage_key,
    )
    logger.info("Deleted file from S3: %s", storage_key)
