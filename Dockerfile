FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY backend-toolkit-auth /workspace/backend-toolkit-auth
COPY backend-toolkit-config /workspace/backend-toolkit-config
COPY backend-toolkit-database /workspace/backend-toolkit-database
COPY backend-toolkit-logger /workspace/backend-toolkit-logger
COPY backend-toolkit-storage /workspace/backend-toolkit-storage
COPY backend-toolkit-example /workspace/backend-toolkit-example

WORKDIR /workspace/backend-toolkit-example

RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
