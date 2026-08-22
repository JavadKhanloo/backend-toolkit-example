# backend-toolkit-example

Template FastAPI app that wires the toolkit packages with a Repository / Unit of Work layout. Notes have a single **cover** file and many **files**, stored in a shared `attachments` table (see [GUIDE.md](GUIDE.md)).

- `backend-toolkit-config` — typed `.env` settings
- `backend-toolkit-logger` — request-scoped structured logs
- `backend-toolkit-database` — PostgreSQL via SQLAlchemy 2
- `backend-toolkit-storage` — local files or MinIO, plus `attachment_field()`
- `backend-toolkit-auth` — Keycloak login, JWT validation, and role checks

## Docker Compose (recommended)

This stack starts PostgreSQL, MinIO, Keycloak (with the `app` realm), and the API:

```bash
docker compose up --build
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

| Service | URL |
| --- | --- |
| API | http://127.0.0.1:8000 |
| Keycloak | http://127.0.0.1:8080 (admin / admin) |
| MinIO console | http://127.0.0.1:9001 (minioadmin / minioadmin) |
| PostgreSQL | localhost:5432 (`app` database) |

Demo users in the imported `app` realm:

| Username | Password | Roles |
| --- | --- | --- |
| `alice` | `alice-password` | `user` |
| `admin` | `admin-password` | `user`, `admin` |

```bash
TOKEN=$(curl -s http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice-password"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/auth/me -H "Authorization: Bearer $TOKEN"
curl -X POST http://127.0.0.1:8000/notes \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=hello" -F "body=from the toolkit" -F "cover=@README.md"
curl http://127.0.0.1:8000/notes -H "Authorization: Bearer $TOKEN"
```

Delete endpoints need the admin user. Infrastructure only (run the API with `uv` on the host):

```bash
docker compose up postgres minio keycloak keycloak-init
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Local setup without Compose

- Python 3.14+
- PostgreSQL on `localhost:5432` with database `app`
- Keycloak on `localhost:8080` with realm `app` and client `backend`
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
| `POST` | `/auth/login` | public | Password grant against Keycloak |
| `POST` | `/auth/refresh` | public | Exchange a refresh token |
| `POST` | `/auth/logout` | public | Invalidate a refresh token |
| `GET` | `/auth/me` | bearer | Current user from the access token |
| `POST` | `/notes` | bearer | Create a note (`title`, `body`, optional `cover`, optional `files`) |
| `GET` | `/notes` | bearer | List notes with attachment metadata |
| `GET` | `/notes/{id}` | bearer | Read one note |
| `DELETE` | `/notes/{id}` | admin | Delete the note, attachment rows, and stored files |
| `POST` | `/notes/{id}/cover` | bearer | Replace the cover file |
| `POST` | `/notes/{id}/files` | bearer | Add more files |
| `GET` | `/notes/{id}/attachments/{attachment_id}` | bearer | Download one file |
| `DELETE` | `/notes/{id}/attachments/{attachment_id}` | admin | Remove one file |

Logs go to the console and `logs/app.log`. How to add another entity with files is documented in [GUIDE.md](GUIDE.md).
