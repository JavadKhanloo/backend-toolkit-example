from backend_toolkit_pagination import PageParams, paginate
from fastapi.testclient import TestClient

from app.exceptions import NoteNotFoundError
from app.services import NoteService
from tests.conftest import create_example_app, login


class InMemoryNotes:
    def __init__(self) -> None:
        self.items: list[object] = []
        self._next_id = 1

    async def add(self, record):
        record.id = self._next_id
        record.cover = None
        record.files = []
        self._next_id += 1
        self.items.append(record)
        return record

    async def list(self, **filters):
        return list(self.items)

    async def list_page(self, params: PageParams, **filters):
        return paginate(self.items, params)

    async def get_by_id(self, id: int):
        return next((item for item in self.items if item.id == id), None)

    async def delete(self, id: int) -> None:
        self.items = [item for item in self.items if item.id != id]


class InMemoryUow:
    def __init__(self) -> None:
        self.notes = InMemoryNotes()
        self.session = type("Session", (), {"expire_all": lambda self: None})()

    async def commit(self) -> None:
        return None


async def test_note_service_creates_and_deletes_notes():
    service = NoteService(uow=InMemoryUow(), storage=None)
    note = await service.create_note("hello", "from tests")
    assert note.id == 1
    assert note.title == "hello"
    listed = await service.list_notes(PageParams())
    assert [item.title for item in listed.items] == ["hello"]
    await service.delete_note(1)
    try:
        await service.get_note(1)
        raise AssertionError("expected missing note")
    except NoteNotFoundError:
        pass


def test_notes_require_login_and_admin_to_delete():
    with TestClient(create_example_app()) as client:
        anonymous = client.get("/notes")
        assert anonymous.status_code == 401

        alice = login(client, "alice", "alice-password")
        created = client.post(
            "/notes",
            headers={"Authorization": f"Bearer {alice}"},
            data={"title": "hello", "body": "from the toolkit"},
        )
        assert created.status_code == 200
        note_id = created.json()["id"]

        listed = client.get(
            "/notes",
            headers={"Authorization": f"Bearer {alice}"},
            params={"page": 1, "page_size": 10},
        )
        assert listed.status_code == 200
        body = listed.json()
        assert body["total"] == 1
        assert body["page"] == 1
        assert body["items"][0]["id"] == note_id

        forbidden = client.delete(
            f"/notes/{note_id}",
            headers={"Authorization": f"Bearer {alice}"},
        )
        assert forbidden.status_code == 403

        admin = login(client, "admin", "admin-password")
        deleted = client.delete(
            f"/notes/{note_id}",
            headers={"Authorization": f"Bearer {admin}"},
        )
        assert deleted.status_code == 204
