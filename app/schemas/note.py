from pydantic import BaseModel, ConfigDict, Field

from app.schemas.attachment import AttachmentRead


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    cover: AttachmentRead | None = None
    files: list[AttachmentRead] = Field(default_factory=list)
