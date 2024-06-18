from abc import ABC, abstractmethod

from discord.message import Message


class IAttachmentHandler(ABC):
    _attachment_max_size: int = 1024 * 1024 * 500

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

    @property
    def max_size(self) -> int:
        """
        The maximum size of an attachment in bytes
        Returns
        -------
        int
        """
        return self._attachment_max_size

    @max_size.setter
    def max_size(self, value: int):
        """
        Set the maximum size of an attachment in bytes
        """
        self._attachment_max_size = value
