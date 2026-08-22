class AppError(Exception):
    """Base error for the example application."""


class NoteNotFoundError(AppError):
    def __init__(self, note_id: int) -> None:
        super().__init__(f"Note {note_id} was not found")
        self.note_id = note_id


class AttachmentNotFoundError(AppError):
    def __init__(self, attachment_id: int) -> None:
        super().__init__(f"Attachment {attachment_id} was not found")
        self.attachment_id = attachment_id
