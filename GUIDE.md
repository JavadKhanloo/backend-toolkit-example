# Architecture guide

This example is a template for new backends. It follows the Repository and Unit of Work patterns described in [this article](https://dev.to/manukanne/a-python-implementation-of-the-unit-of-work-and-repository-design-pattern-using-sqlmodel-3mb5), implemented with SQLAlchemy 2 (not SQLModel) and the backend-toolkit packages.

## Layout

```
app/
  main.py                 FastAPI app, toolkit setup, routers
  dependencies.py         Unit of Work and service injection
  exceptions.py           Domain errors mapped to HTTP 404 in routers
  models/                 SQLAlchemy tables
  schemas/                Pydantic request/response models
  repositories/           Persistence only (no HTTP, no storage I/O)
  services/               Use cases + Unit of Work
  routers/                HTTP adapters (FastAPI)
```

Routers never talk to SQLAlchemy or S3 directly. They call a service. The service uses repositories through one Unit of Work.

```
Router  →  Service  →  UnitOfWork
                         ├─ NoteRepository
                         ├─ AttachmentRepository
                         └─ Storage (files, after commit)
```

## Toolkits

| Package | Role in this app |
| --- | --- |
| `backend-toolkit-config` | Typed `.env` (`DATABASE__*`, `STORAGE__*`, `AUTH__*`, …) |
| `backend-toolkit-logger` | Request-scoped structured logs |
| `backend-toolkit-database` | Async engine, `Base`, `get_session`, Alembic (`toolkit-db`) |
| `backend-toolkit-pagination` | `Page` / `page` / `page_size` for every list endpoint |
| `backend-toolkit-storage` | File/S3 blobs + `attachment_field()` |
| `backend-toolkit-auth` | Login, user/role admin at `/users` and `/roles`, `get_current_user` / `require_roles` |

## Adding a model with files (Django-style)

Declare fields on the SQLAlchemy model. A shared `attachments` table is created on the same `Base`:

```python
from backend_toolkit_database import Base
from backend_toolkit_storage import attachment_field, get_attachment_model
from sqlalchemy.orm import Mapped, mapped_column

Attachment = get_attachment_model(Base)

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str]
    pdf = attachment_field()                 # one file
    scans = attachment_field(multiple=True)  # many files
```

Then copy the Note stack:

1. `repositories/invoice.py` — inherit `GenericSqlRepository`
2. Expose it on `UnitOfWork`
3. `services/invoice.py` — create/update/delete, call `store_attachment` after `flush`
4. `routers/invoices.py` — multipart form + `Depends(get_invoice_service)` + `Depends(get_current_user)`
5. Export the model from `app.models` so Alembic autogenerate sees the table, then `toolkit-db revision -m "..."` and `toolkit-db upgrade`

`GenericSqlRepository.delete` already calls `delete_attachments_for`. After `uow.commit()`, queued blobs are removed from disk or MinIO. Deleting a parent row therefore removes both attachment rows and stored files.

## Unit of Work

`UnitOfWork` opens one `AsyncSession` per request. All repositories share it.

- `commit()` writes the transaction, then deletes stored files for removed `Attachment` rows
- If the handler raises, `__aexit__` rolls back and **does not** delete files
- Call `commit()` only from the service after the use case succeeds

Do not commit inside a repository.

## Requests

`POST /notes` is `multipart/form-data` so Swagger can upload files:

- `title`, `body` — text
- `cover` — optional single file
- `files` — optional extra files (choose multiple)

`GET /notes` returns a `Page` (`items`, `total`, `page`, `page_size`, `pages`, `has_next`, `has_previous`). The same envelope is used by `/users` and `/roles`.

`GET /notes/{id}` returns nested `cover` and `files` metadata. Download bytes from `GET /notes/{id}/attachments/{attachment_id}`.

Note routes require a bearer token. Get one from `POST /auth/login`, then click Authorize in Swagger. Delete endpoints require the `admin` role.

## Authentication and identity

`setup_fastapi` from `backend-toolkit-auth` mounts login routes under `/auth` and identity admin routes under `/users` and `/roles`. After the stack starts, log in as `admin` and create users, roles, and assignments from FastAPI. Callers do not use the identity provider UI.

Routers inject `CurrentUser` with `Depends(get_current_user)` or `Depends(require_roles("admin"))`.

## Migrations

`backend-toolkit-database` owns Alembic. This app only keeps `alembic.ini`, `alembic/env.py`, and revision files.

```bash
uv run toolkit-db revision -m "add invoices"
uv run toolkit-db upgrade
uv run toolkit-db current
```

`app/main.py` calls `setup_database(..., run_migrations=True)`, and the Docker image runs `python -m backend_toolkit_database upgrade` before uvicorn. Prefer the CLI in production so multiple workers do not race.

Do not turn `auto_create_tables` back on once revisions exist. If the database was created by that flag, run `uv run toolkit-db stamp head` once.
