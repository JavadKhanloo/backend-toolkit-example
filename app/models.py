from sqlalchemy.orm import Mapped, mapped_column

from backend_toolkit_database import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    body: Mapped[str]
    attachment_key: Mapped[str | None] = mapped_column(default=None)
    attachment_filename: Mapped[str | None] = mapped_column(default=None)
    attachment_content_type: Mapped[str | None] = mapped_column(default=None)
