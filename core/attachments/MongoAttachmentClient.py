import asyncio
import datetime
from typing import Any, Final

from discord.message import Attachment, Message
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.results import InsertOneResult

from core.attachments.AttachmentHandler import IAttachmentHandler
from core.attachments.errors import AttachmentSizeException
from core.models import getLogger


def _mongo_attachment_dict(attachment: Attachment, data: bytes) -> dict:
    """
    Convert a discord attachment to a dict that can be stored in the database
    Parameters
    ----------
    attachment
    data

    Returns
    -------
    dict
    """
    return {
        # same as discord id
        "_id": attachment.id,
        "filename": attachment.filename,
        "content_type": attachment.content_type,
        "width": attachment.width,
        "height": attachment.height,
        "description": attachment.description,
        "size": attachment.size,
        "data": data,
        "uploaded_at": datetime.datetime.now(datetime.timezone.utc),
    }


class MongoAttachmentHandler(IAttachmentHandler):
    logger = getLogger(__name__)

    # 8 MB to bytes
    MONGODB_MAX_SIZE: Final[int] = 1024 * 1024 * 15

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.client = database
        self.attachment_collection: AsyncIOMotorCollection = database["attachments"]
        self._attachment_max_size = self.MONGODB_MAX_SIZE
        # self.log_collection: AsyncIOMotorCollection = database["logs"]

    @IAttachmentHandler.max_size.setter
    def max_size(self, size: int) -> None:
        if size > self.MONGODB_MAX_SIZE:
            self.logger.warning(
                f"MongoDB attachment storage has a maximum attachment size of {self.MONGODB_MAX_SIZE} bytes. "
                f"The max attachment size will be set to this value.."
            )
            return
        self._attachment_max_size = size

    async def _store_attachments_bulk(self, attachments: list[Attachment]) -> Any:
        attachment_data = await asyncio.gather(*[attachment.read() for attachment in attachments])

        results = await self.attachment_collection.insert_many(
            [
                _mongo_attachment_dict(attachment, attachment_data[index])
                for index, attachment in enumerate(attachments)
            ]
        )

        return results.inserted_ids

    async def _store_attachment(self, attachment: Attachment) -> Any:
        result: InsertOneResult = await self.attachment_collection.insert_one(
            _mongo_attachment_dict(attachment, await attachment.read())
        )
        return result.inserted_id

    async def upload_attachments(
        self,
        message: Message,
    ) -> list[dict]:
        attachments = []

        for attachment in message.attachments:
            if attachment.size > self.max_size:
                self.logger.warning(
                    "Attachment %s is too large to be stored in the database. It will not be uploaded...",
                    attachment.filename,
                )
                raise AttachmentSizeException("Attachment too large")

        if len(message.attachments) > 1:
            await self._store_attachments_bulk(message.attachments)
        else:
            await self._store_attachment(message.attachments[0])

        for attachment in message.attachments:
            attachments.append(
                {
                    "id": attachment.id,
                    "filename": attachment.filename,
                    "type": "internal",
                    # URL points to the original discord URL
                    "url": attachment.url,
                    "content_type": attachment.content_type,
                    "width": attachment.width,
                    "height": attachment.height,
                }
            )

        return attachments
