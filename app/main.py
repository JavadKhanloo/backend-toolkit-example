from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from backend_toolkit_config import AppSettings, get_settings
from backend_toolkit_database import get_session, setup_fastapi as setup_database
from backend_toolkit_logger import get_logger, setup_fastapi as setup_logging
from backend_toolkit_storage import (
    Storage,
    StorageObjectNotFoundError,
    get_storage,
    setup_fastapi as setup_storage,
)

from app.models import Note


class NoteCreate(BaseModel):
    title: str
    body: str


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    attachment_filename: str | None = None
    attachment_content_type: str | None = None


settings = get_settings()

app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
)

setup_logging(app)
setup_database(
    app,
    settings=settings.database,
    auto_create_tables=True,
)
setup_storage(app, settings=settings.storage)

logger = get_logger(__name__)


async def _get_note(note_id: int, session: AsyncSession) -> Note:
    note = await session.get(Note, note_id)

    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


@app.get("/health")
async def health(
    settings: AppSettings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
    storage: Storage = Depends(get_storage),
) -> dict[str, object]:
    await session.execute(select(1))
    await storage.ping()
    logger.info("health_checked")
    return {
        "status": "ok",
        "name": settings.app.name,
        "environment": settings.app.environment.value,
        "debug": settings.app.debug,
        "database": "ok",
        "storage": storage.backend.name,
    }


@app.post("/notes", response_model=NoteRead)
async def create_note(
    payload: NoteCreate,
    session: AsyncSession = Depends(get_session),
) -> Note:
    note = Note(title=payload.title, body=payload.body)
    session.add(note)
    await session.commit()
    await session.refresh(note)
    logger.info("note_created", note_id=note.id, title=note.title)
    return note


@app.get("/notes", response_model=list[NoteRead])
async def list_notes(
    session: AsyncSession = Depends(get_session),
) -> list[Note]:
    result = await session.execute(select(Note).order_by(Note.id))
    notes = list(result.scalars())
    logger.info("notes_listed", count=len(notes))
    return notes


@app.get("/notes/{note_id}", response_model=NoteRead)
async def read_note(
    note_id: int,
    session: AsyncSession = Depends(get_session),
) -> Note:
    return await _get_note(note_id, session)


@app.post("/notes/{note_id}/attachment", response_model=NoteRead)
async def upload_attachment(
    note_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    storage: Storage = Depends(get_storage),
) -> Note:
    note = await _get_note(note_id, session)
    filename = file.filename or "attachment"
    key = f"notes/{note.id}/{filename}"
    data = await file.read()

    if note.attachment_key and note.attachment_key != key:
        await storage.delete(note.attachment_key)

    stored = await storage.put(
        key,
        data,
        content_type=file.content_type,
    )
    note.attachment_key = stored.key
    note.attachment_filename = filename
    note.attachment_content_type = stored.content_type
    await session.commit()
    await session.refresh(note)
    logger.info(
        "note_attachment_uploaded",
        note_id=note.id,
        key=stored.key,
        size=stored.size,
    )
    return note


@app.get("/notes/{note_id}/attachment")
async def download_attachment(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    storage: Storage = Depends(get_storage),
) -> Response:
    note = await _get_note(note_id, session)

    if note.attachment_key is None:
        raise HTTPException(status_code=404, detail="Note has no attachment")

    try:
        stored = await storage.get(note.attachment_key)
    except StorageObjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    headers = {}
    if note.attachment_filename:
        headers["Content-Disposition"] = (
            f'attachment; filename="{note.attachment_filename}"'
        )

    return Response(
        content=stored.content,
        media_type=note.attachment_content_type
        or stored.content_type
        or "application/octet-stream",
        headers=headers,
    )


@app.delete("/notes/{note_id}/attachment", response_model=NoteRead)
async def delete_attachment(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    storage: Storage = Depends(get_storage),
) -> Note:
    note = await _get_note(note_id, session)

    if note.attachment_key is not None:
        await storage.delete(note.attachment_key)

    note.attachment_key = None
    note.attachment_filename = None
    note.attachment_content_type = None
    await session.commit()
    await session.refresh(note)
    logger.info("note_attachment_deleted", note_id=note.id)
    return note
