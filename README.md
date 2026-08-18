# backend-toolkit-example

Minimal FastAPI app that wires together:

- `backend-toolkit-config` for typed `.env` settings
- `backend-toolkit-logger` for request-scoped structured logs
- `backend-toolkit-database` for PostgreSQL via SQLAlchemy 2

## Requirements

- Python 3.14+
- PostgreSQL on `localhost:5432`

Create the `app` database once:

```sql
CREATE DATABASE app;
```

## Setup

```bash
cp .env.example .env
```

Edit `DATABASE__URL` in `.env` if your PostgreSQL user or password is not `postgres` / `postgres`.

```bash
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | App settings plus a `SELECT 1` database ping |
| `POST` | `/notes` | Create a note |
| `GET` | `/notes` | List notes |

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d "{\"title\":\"hello\",\"body\":\"from the toolkit\"}"
curl http://127.0.0.1:8000/notes
```

Logs go to the console and to `logs/app.log`.
