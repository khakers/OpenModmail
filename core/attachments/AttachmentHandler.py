from abc import ABC, abstractmethod

from discord.message import Message


class IAttachmentHandler(ABC):
    @abstractmethod
    async def upload_attachments(self, message: Message) -> list[dict]:
        """
        Uploads all attachments from a message to the database
        Parameters
        ----------
        message
        Returns
        -------
        A dict containing what should be appended to the thread documents attachments field
        """
        pass
