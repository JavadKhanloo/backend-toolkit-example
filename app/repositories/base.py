from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from backend_toolkit_pagination import Page, PageParams
from backend_toolkit_pagination.sqlalchemy import paginate_select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_toolkit_storage import attachment_load_options, delete_attachments_for

T = TypeVar("T")


class GenericRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, id: int) -> T | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, **filters: Any) -> list[T]:
        raise NotImplementedError

    @abstractmethod
    async def list_page(self, params: PageParams, **filters: Any) -> Page[T]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, record: T) -> T:
        raise NotImplementedError

    @abstractmethod
    async def update(self, record: T) -> T:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: int) -> None:
        raise NotImplementedError


class GenericSqlRepository(GenericRepository[T]):
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None:
        stmt = (
            select(self.model)
            .where(self.model.id == id)
            .options(*attachment_load_options(self.model))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, **filters: Any) -> list[T]:
        stmt = select(self.model)
        for key, value in filters.items():
            column = getattr(self.model, key, None)
            if column is None:
                raise ValueError(f"Unknown filter {key!r} for {self.model.__name__}")
            stmt = stmt.where(column == value)

        stmt = stmt.options(*attachment_load_options(self.model)).order_by(
            self.model.id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def list_page(self, params: PageParams, **filters: Any) -> Page[T]:
        stmt = select(self.model)
        for key, value in filters.items():
            column = getattr(self.model, key, None)
            if column is None:
                raise ValueError(f"Unknown filter {key!r} for {self.model.__name__}")
            stmt = stmt.where(column == value)

        stmt = stmt.options(*attachment_load_options(self.model)).order_by(
            self.model.id
        )
        return await paginate_select(self.session, stmt, params, unique=True)

    async def add(self, record: T) -> T:
        self.session.add(record)
        await self.session.flush()
        return record

    async def update(self, record: T) -> T:
        await self.session.flush()
        return record

    async def delete(self, id: int) -> None:
        record = await self.get_by_id(id)
        if record is None:
            return

        if getattr(self.model, "__attachment_fields__", None):
            await delete_attachments_for(self.session, record)

        await self.session.delete(record)
