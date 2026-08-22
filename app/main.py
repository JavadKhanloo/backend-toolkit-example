from backend_toolkit_auth import setup_fastapi as setup_auth
from backend_toolkit_config import get_settings
from backend_toolkit_database import setup_fastapi as setup_database
from backend_toolkit_logger import setup_fastapi as setup_logging
from backend_toolkit_storage import setup_fastapi as setup_storage
from fastapi import FastAPI

from app.models import Attachment, Note
from app.routers import health_router, notes_router

settings = get_settings()

app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
)

setup_logging(app)
setup_database(
    app,
    settings=settings.database,
    run_migrations=True,
)
setup_storage(app, settings=settings.storage)
setup_auth(app, settings=settings.auth)

app.include_router(health_router)
app.include_router(notes_router)

_ = (Note, Attachment)
