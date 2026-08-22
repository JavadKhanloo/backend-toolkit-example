from backend_toolkit_auth import AuthSettings, MemoryBackend, setup_fastapi
from backend_toolkit_pagination import PaginationSettings
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import login


def _app() -> FastAPI:
    app = FastAPI()
    setup_fastapi(
        app,
        AuthSettings(backend="memory", _env_file=None),
        backend=MemoryBackend(),
        page_settings=PaginationSettings(
            default_page_size=20,
            max_page_size=100,
            _env_file=None,
        ),
    )
    return app


def test_admin_manages_users_and_roles_from_fastapi():
    with TestClient(_app()) as client:
        alice = login(client, "alice", "alice-password")
        denied = client.get("/users", headers={"Authorization": f"Bearer {alice}"})
        assert denied.status_code == 403

        admin = login(client, "admin", "admin-password")
        headers = {"Authorization": f"Bearer {admin}"}

        users = client.get(
            "/users",
            headers=headers,
            params={"page": 1, "page_size": 10},
        )
        assert users.status_code == 200
        listed = users.json()
        assert listed["total"] == 2
        assert listed["page"] == 1
        assert listed["page_size"] == 10
        assert {user["username"] for user in listed["items"]} == {"admin", "alice"}

        paged = client.get(
            "/users",
            headers=headers,
            params={"page": 1, "page_size": 1},
        )
        assert paged.status_code == 200
        assert paged.json()["pages"] == 2
        assert len(paged.json()["items"]) == 1
        assert paged.json()["has_next"] is True

        role = client.post(
            "/roles",
            headers=headers,
            json={"name": "editor", "description": "Can edit notes"},
        )
        assert role.status_code == 201

        created = client.post(
            "/users",
            headers=headers,
            json={
                "username": "bob",
                "password": "bob-password",
                "email": "bob@example.com",
                "first_name": "Bob",
                "last_name": "Notes",
                "roles": ["user", "editor"],
            },
        )
        assert created.status_code == 201
        user_id = created.json()["id"]
        assert set(created.json()["roles"]) == {"user", "editor"}

        bob = login(client, "bob", "bob-password")
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {bob}"})
        assert me.status_code == 200
        assert set(me.json()["roles"]) == {"user", "editor"}

        unassigned = client.delete(
            f"/users/{user_id}/roles/editor",
            headers=headers,
        )
        assert unassigned.status_code == 200
        assert unassigned.json()["roles"] == ["user"]

        deleted = client.delete(f"/users/{user_id}", headers=headers)
        assert deleted.status_code == 204
        gone = client.delete("/roles/editor", headers=headers)
        assert gone.status_code == 204
