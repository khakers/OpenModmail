from discord import Message

from core.attachments.attachment_handler import IAttachmentHandler, ThreadAttachment

"""
        Attachment handler client that functions the same as the default modmail system.
"""


class NoopAttachmentHandler(IAttachmentHandler):
    async def upload_attachments(self, message: Message) -> list[dict]:
        return [
            {
                "id": a.id,
                "filename": a.filename,
                "is_image": a.content_type.startswith("image/"),
                "size": a.size,
                "url": a.url,
                "content_type": a.content_type,
            }
            for a in message.attachments
        ]
