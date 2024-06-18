class AttachmentSizeException(Exception):
    """Raised when an attachment is too large.
    Attributes:
            size -- size of the attachment
            max -- maximum allowed size of the attachment
            message -- explanation of why the specific transition is invalid
    """

    def __init__(self, size: int, max_size: int, message: str):
        self.size = size
        self.max = max_size
        self.message = message
        super().__init__(self.message)
