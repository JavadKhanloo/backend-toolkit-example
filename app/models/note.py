from sqlalchemy.orm import Mapped, mapped_column

from backend_toolkit_database import Base
from backend_toolkit_storage import attachment_field, get_attachment_model

Attachment = get_attachment_model(Base)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    body: Mapped[str]
    cover = attachment_field()
    files = attachment_field(multiple=True)
