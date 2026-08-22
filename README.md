# backend-toolkit-example

Template FastAPI app that wires the toolkit packages with a Repository / Unit of Work layout. Notes have a single **cover** file and many **files**, stored in a shared `attachments` table (see [GUIDE.md](GUIDE.md)).

- `backend-toolkit-config` — typed `.env` settings
- `backend-toolkit-logger` — request-scoped structured logs
- `backend-toolkit-database` — PostgreSQL via SQLAlchemy 2
- `backend-toolkit-storage` — local files or MinIO, plus `attachment_field()`
- `backend-toolkit-auth` — login, current user, and admin user/role CRUD

## Docker Compose (recommended)

This stack starts PostgreSQL, MinIO, the identity provider, and the API:

```bash
docker compose up --build
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

| Service | URL |
| --- | --- |
| API | http://127.0.0.1:8000 |
| MinIO console | http://127.0.0.1:9001 (minioadmin / minioadmin) |
| PostgreSQL | localhost:5432 (`app` database) |

The first admin is seeded so you can manage everyone else from FastAPI:

| Username | Password | Roles |
| --- | --- | --- |
| `admin` | `admin-password` | `user`, `admin` |
| `alice` | `alice-password` | `user` |

Log in as `admin`, then create users and roles from `/users` and `/roles`. Do not open the identity-provider console to manage the application.

```bash
TOKEN=$(curl -s http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin-password"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/users -H "Authorization: Bearer $TOKEN"
curl -X POST http://127.0.0.1:8000/roles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"editor","description":"Can edit notes"}'
curl -X POST http://127.0.0.1:8000/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","password":"bob-password","email":"bob@example.com","first_name":"Bob","last_name":"Notes","roles":["user","editor"]}'
curl -X POST http://127.0.0.1:8000/notes \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=hello" -F "body=from the toolkit" -F "cover=@README.md"
```

Delete note endpoints need the `admin` role. Infrastructure only (run the API with `uv` on the host):

```bash
docker compose up postgres minio keycloak keycloak-init
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Local setup without Compose

- Python 3.14+
- PostgreSQL on `localhost:5432` with database `app`
- Optional MinIO on `localhost:9000`

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If you ran the previous notes schema, drop it once:

```sql
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS attachments;
```

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | public | Settings plus database, storage, and auth ping |
| `POST` | `/auth/login` | public | Login and issue tokens |
| `POST` | `/auth/refresh` | public | Exchange a refresh token |
| `POST` | `/auth/logout` | public | Invalidate a refresh token |
| `GET` | `/auth/me` | bearer | Current user from the access token |
| `GET` | `/users` | admin | List users |
| `POST` | `/users` | admin | Create a user |
| `GET` | `/users/{id}` | admin | Read one user |
| `PATCH` | `/users/{id}` | admin | Update a user |
| `DELETE` | `/users/{id}` | admin | Delete a user |
| `POST` | `/users/{id}/roles` | admin | Add roles |
| `PUT` | `/users/{id}/roles` | admin | Replace roles |
| `DELETE` | `/users/{id}/roles/{name}` | admin | Remove one role |
| `GET` | `/roles` | admin | List roles |
| `POST` | `/roles` | admin | Create a role |
| `GET` | `/roles/{name}` | admin | Read one role |
| `PATCH` | `/roles/{name}` | admin | Update a role |
| `DELETE` | `/roles/{name}` | admin | Delete a role |
| `POST` | `/notes` | bearer | Create a note (`title`, `body`, optional `cover`, optional `files`) |
| `GET` | `/notes` | bearer | List notes with attachment metadata |
| `GET` | `/notes/{id}` | bearer | Read one note |
| `DELETE` | `/notes/{id}` | admin | Delete the note, attachment rows, and stored files |
| `POST` | `/notes/{id}/cover` | bearer | Replace the cover file |
| `POST` | `/notes/{id}/files` | bearer | Add more files |
| `GET` | `/notes/{id}/attachments/{attachment_id}` | bearer | Download one file |
| `DELETE` | `/notes/{id}/attachments/{attachment_id}` | admin | Remove one file |

Logs go to the console and `logs/app.log`. How to add another entity with files is documented in [GUIDE.md](GUIDE.md).

```bash
uv sync --group dev
uv run pytest -q
```
