from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Note
from app.repositories.base import GenericRepository, GenericSqlRepository


class NoteRepositoryBase(GenericRepository[Note], ABC):
    @abstractmethod
    async def get_by_title(self, title: str) -> Note | None:
        raise NotImplementedError


class NoteRepository(GenericSqlRepository[Note], NoteRepositoryBase):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Note)

    async def get_by_title(self, title: str) -> Note | None:
        notes = await self.list(title=title)
        return notes[0] if notes else None
