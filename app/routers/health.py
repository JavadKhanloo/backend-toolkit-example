from backend_toolkit_auth import Auth, get_auth
from backend_toolkit_config import AppSettings, get_settings
from backend_toolkit_database import get_session
from backend_toolkit_logger import get_logger
from backend_toolkit_storage import Storage, get_storage
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health")
async def health(
    settings: AppSettings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
    storage: Storage = Depends(get_storage),
    auth: Auth = Depends(get_auth),
) -> dict[str, object]:
    await session.execute(select(1))
    await storage.ping()
    await auth.ping()
    logger.info("health_checked")
    return {
        "status": "ok",
        "name": settings.app.name,
        "environment": settings.app.environment.value,
        "debug": settings.app.debug,
        "database": "ok",
        "storage": storage.backend.name,
        "auth": auth.backend.name,
    }
