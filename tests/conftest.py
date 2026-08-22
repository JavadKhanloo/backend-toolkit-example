from types import SimpleNamespace

from backend_toolkit_auth import AuthSettings, MemoryBackend, setup_fastapi
from backend_toolkit_pagination import Page, PageParams, PaginationSettings, paginate
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dependencies import get_note_service
from app.pagination import configure_pagination
from app.exceptions import NoteNotFoundError
from app.routers import notes_router


class FakeNoteService:
    def __init__(self) -> None:
        self.notes: dict[int, SimpleNamespace] = {}
        self._next_id = 1

    async def list_notes(self, params: PageParams) -> Page[SimpleNamespace]:
        return paginate(list(self.notes.values()), params)

    async def get_note(self, note_id: int) -> SimpleNamespace:
        note = self.notes.get(note_id)
        if note is None:
            raise NoteNotFoundError(note_id)
        return note

    async def create_note(self, title: str, body: str, cover=None, files=None):
        note = SimpleNamespace(
            id=self._next_id,
            title=title,
            body=body,
            cover=None,
            files=[],
        )
        self.notes[note.id] = note
        self._next_id += 1
        return note

    async def delete_note(self, note_id: int) -> None:
        await self.get_note(note_id)
        del self.notes[note_id]


def create_example_app(service: FakeNoteService | None = None) -> FastAPI:
    page_settings = PaginationSettings(
        default_page_size=20,
        max_page_size=100,
        _env_file=None,
    )
    configure_pagination(page_settings)
    app = FastAPI(title="Toolkit Example Tests")
    setup_fastapi(
        app,
        AuthSettings(backend="memory", _env_file=None),
        backend=MemoryBackend(),
        page_settings=page_settings,
    )
    app.include_router(notes_router)
    fake = service or FakeNoteService()
    app.dependency_overrides[get_note_service] = lambda: fake
    app.state.notes = fake
    return app


def login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
