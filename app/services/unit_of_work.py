from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend_toolkit_storage import (
    Storage,
    pop_storage_deletes,
    purge_stored_files,
)

from app.repositories import (
    AttachmentRepository,
    AttachmentRepositoryBase,
    NoteRepository,
    NoteRepositoryBase,
)


class UnitOfWorkBase(ABC):
    notes: NoteRepositoryBase
    attachments: AttachmentRepositoryBase
    session: AsyncSession

    @abstractmethod
    async def __aenter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, *exc: object) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError


class UnitOfWork(UnitOfWorkBase):
    """
    One request, one transaction.

    Repositories share this session. File blobs are removed from storage
    only after the database commit succeeds.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | Callable[[], AsyncSession],
        storage: Storage,
    ) -> None:
        self._session_factory = session_factory
        self.storage = storage
        self._committed = False

    async def __aenter__(self) -> Self:
        self.session = self._session_factory()
        self.notes = NoteRepository(self.session)
        self.attachments = AttachmentRepository(self.session)
        self._committed = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        try:
            if exc_type is not None or not self._committed:
                await self.rollback()
        finally:
            await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()
        keys = pop_storage_deletes(self.session)
        await purge_stored_files(self.storage, keys)
        self._committed = True

    async def rollback(self) -> None:
        if self.session.in_transaction():
            await self.session.rollback()
        self._committed = False
