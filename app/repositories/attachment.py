from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attachment
from app.repositories.base import GenericRepository, GenericSqlRepository


class AttachmentRepositoryBase(GenericRepository[Attachment], ABC):
    pass


class AttachmentRepository(GenericSqlRepository[Attachment], AttachmentRepositoryBase):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Attachment)
