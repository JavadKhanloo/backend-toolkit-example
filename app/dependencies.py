from collections.abc import AsyncIterator

from backend_toolkit_database import get_database
from backend_toolkit_storage import Storage, get_storage
from fastapi import Depends

from app.services import NoteService, UnitOfWork


async def get_uow() -> AsyncIterator[UnitOfWork]:
    uow = UnitOfWork(
        session_factory=get_database().session_factory,
        storage=get_storage(),
    )
    async with uow:
        yield uow


def get_note_service(
    uow: UnitOfWork = Depends(get_uow),
    storage: Storage = Depends(get_storage),
) -> NoteService:
    return NoteService(uow=uow, storage=storage)
