import datetime
import io

from discord import Message
from minio import Minio
from minio.commonconfig import Tags

from core.attachments.AttachmentHandler import IAttachmentHandler


class S3AttachmentHandler(IAttachmentHandler):
    def __init__(
        self,
        endpoint: str,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str | None = None,
        bucket: str | None = "modmail-attachments",
    ) -> None:
        """
        Initialize the S3AttachmentHandler with the given access key, secret key, and endpoint.

        Parameters
        ----------
        access_key : str | None
            The access key for the S3 bucket.
        secret_key : str | None
            The secret key for the S3 bucket.
        endpoint : str
            The endpoint for the S3 bucket.
        """
        self.bucket = bucket
        self.region = region

        self.client = Minio(
            endpoint, access_key=access_key, secret_key=secret_key, secure=False, region=region
        )
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def upload_attachments(self, message: Message) -> list[dict]:
        """
        Upload attachments from a given message to the S3 bucket.

        Parameters
        ----------
        message : Message
            The message containing the attachments to upload.

        Returns
        -------
        list[dict]
            A list of dictionaries containing information about the uploaded attachments.
        """
        attachments = []

        # Setup metadata for S3 object
        tags = Tags.new_object_tags()
        tags["message_id"] = str(message.id)
        tags["channel_id"] = str(message.channel.id)
        # tags["bot_id"] = str(bot.bot_id)
        for attachment in message.attachments:
            if attachment.size > self.max_size:
                raise ValueError(
                    f"Attachment {attachment.filename} is too large. Max size is {self.max_size} bytes."
                )

        for attachment in message.attachments:
            result = self.client.put_object(
                self.bucket,
                str(attachment.id),
                io.BytesIO(await attachment.read()),
                length=attachment.size,
                content_type=attachment.content_type,
                tags=tags,
            )
            attachments.append(
                {
                    "id": attachment.id,
                    "filename": attachment.filename,
                    "type": "s3",
                    "s3_object": result.object_name,
                    "s3_bucket": result.bucket_name,
                    "content_type": attachment.content_type,
                    "width": attachment.width,
                    "height": attachment.height,
                    "description": attachment.description,
                    "size": attachment.size,
                    "uploaded_at": datetime.datetime.now(datetime.timezone.utc),
                }
            )

        return attachments
