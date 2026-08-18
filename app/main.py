from fastapi import Depends, FastAPI
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_toolkit_config import AppSettings, get_settings
from backend_toolkit_database import get_session, setup_fastapi as setup_database
from backend_toolkit_logger import get_logger, setup_fastapi as setup_logging

from app.models import Note


class NoteCreate(BaseModel):
    title: str
    body: str


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str


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

logger = get_logger(__name__)


@app.get("/health")
async def health(
    settings: AppSettings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    await session.execute(select(1))
    logger.info("health_checked")
    return {
        "status": "ok",
        "name": settings.app.name,
        "environment": settings.app.environment.value,
        "debug": settings.app.debug,
        "database": "ok",
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
