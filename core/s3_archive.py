"""
S3 Attachment Archive Service

Handles archival of Discord message attachments to S3 storage.
Provides resilient attachment storage for logs and thread replay.
"""

import asyncio
import logging
import typing
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import aiohttp
from discord import Attachment

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception
    BotoCoreError = Exception

logger = logging.getLogger(__name__)


class S3ArchiveConfig:
    """Configuration for S3 attachment archival."""

    def __init__(
        self,
        enabled: bool,
        bucket: Optional[str],
        region: str,
        access_key_id: Optional[str],
        secret_access_key: Optional[str],
        endpoint: Optional[str] = None,
        key_prefix: str = "modmail/attachments/",
    ):
        self.enabled = enabled
        self.bucket = bucket or "modmail-attachments"
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.endpoint = endpoint
        self.key_prefix = key_prefix or "modmail/attachments/"

    def is_valid(self) -> bool:
        """Check if S3 configuration is valid and complete."""
        if not self.enabled:
            return True

        required = [self.bucket, self.access_key_id, self.secret_access_key]
        return all(required) and BOTO3_AVAILABLE


class S3AttachmentArchiver:
    """Manages archival of message attachments to S3."""

    def __init__(self, config: S3ArchiveConfig):
        self.config = config
        self._client: S3Client | None = None
        self._session = None
        self._presigned_url_expiry = 604800  # 7 days in seconds

    def _get_s3_client(self):
        """Get or create S3 client."""
        if not self.config.is_valid():
            logger.error("S3 archival is not properly configured.")
            return None

        if self._client is not None:
            return self._client

        try:
            session_kwargs = {
                "aws_access_key_id": self.config.access_key_id,
                "aws_secret_access_key": self.config.secret_access_key,
                "region_name": self.config.region,
            }
            session = boto3.Session(**session_kwargs)

            client_kwargs = {}
            if self.config.endpoint:
                client_kwargs["endpoint_url"] = self.config.endpoint

            self._client = session.client("s3", **client_kwargs)
            logger.info("S3 client initialized successfully.")
            return self._client
        except Exception as e:
            logger.error("Failed to initialize S3 client: %s", e)
            return None

    @staticmethod
    async def _download_attachment(url: str, filename: str) -> Optional[bytes]:
        """Download attachment from Discord CDN."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    else:
                        logger.warning("Failed to download attachment from %s: HTTP %d", url, resp.status)
                        return None
        except asyncio.TimeoutError:
            logger.warning("Timeout downloading attachment from %s", url)
            return None
        except Exception as e:
            logger.warning("Error downloading attachment from %s: %s", url, e)
            return None

    async def archive_attachment(
        self,
        attachment: Attachment,
        thread_id: str,
        message_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Archive a single attachment to S3.

        Args:
            attachment: discord.Attachment object
            thread_id: ID of the thread this attachment belongs to
            message_id: ID of the message containing the attachment

        Returns:
            Dictionary with S3 metadata if successful, None otherwise
        """
        if not self.config.enabled or not self.config.is_valid():
            logger.debug("S3 archival disabled or not configured.")
            return None

        client = self._get_s3_client()
        if client is None:
            logger.error("S3 client unavailable; attachment archival skipped.")
            return None

        # Generate S3 key
        # sanitized_filename = quote(attachment.filename, safe="")
        s3_key = f"{self.config.key_prefix}{thread_id}/{attachment.id}"

        # Upload to S3
        try:
            client.put_object(
                Bucket=self.config.bucket,
                Key=s3_key,
                Body=await attachment.read(),
                ContentType=attachment.content_type or "application/octet-stream",
            )
            logger.debug("Archived attachment to S3: %s", s3_key)
            return {
                "archived": True,
                "bucket": self.config.bucket,
                "key": s3_key,
                "archived_at": datetime.now(timezone.utc),
            }
        except (ClientError, BotoCoreError) as e:
            logger.error("S3 upload failed for %s: %s", s3_key, e)
            return None
        except Exception as e:
            logger.error("Unexpected error archiving attachment: %s", e)
            return None

    async def archive_attachments(
        self,
        attachments: list[Attachment],
        thread_id: str,
        message_id: str,
    ) -> Dict[int, Optional[Dict[str, Any]]]:
        """
        Archive multiple attachments concurrently.

        Args:
            attachments: List of discord.Attachment objects
            thread_id: ID of the thread
            message_id: ID of the message

        Returns:
            Dictionary mapping attachment index to archive metadata
        """
        if not self.config.enabled or not self.config.is_valid():
            return {}

        tasks = [self.archive_attachment(att, thread_id, message_id) for att in attachments]

        results = await asyncio.gather(*tasks, return_exceptions=False)
        return {i: result for i, result in enumerate(results)}


async def get_archiver(config_getter) -> Optional[S3AttachmentArchiver]:
    """
    Factory function to create an S3 archiver from bot config.

    Args:
        config_getter: Callable that returns bot config dict

    Returns:
        S3AttachmentArchiver instance if S3 is properly configured, None otherwise
    """
    try:
        config_dict = config_getter() if callable(config_getter) else config_getter
        s3_config = S3ArchiveConfig(
            enabled=config_dict.get("s3_enabled", False),
            bucket=config_dict.get("s3_bucket"),
            region=config_dict.get("s3_region", "us-east-1"),
            access_key_id=config_dict.get("s3_access_key_id"),
            secret_access_key=config_dict.get("s3_secret_access_key"),
            endpoint=config_dict.get("s3_endpoint"),
            key_prefix=config_dict.get("s3_key_prefix", "modmail/attachments/"),
        )

        if not s3_config.is_valid():
            if s3_config.enabled:
                logger.warning("S3 archival enabled but configuration is invalid or incomplete.")
            return None

        return S3AttachmentArchiver(s3_config)
    except Exception as e:
        logger.error("Failed to initialize S3 archiver: %s", e)
        return None
