from sqlalchemy.orm import Mapped, mapped_column

from backend_toolkit_database import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    body: Mapped[str]
