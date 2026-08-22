from typing import Annotated, Any

from backend_toolkit_pagination import PageParams, PaginationSettings, page_params
from fastapi import Query

_resolve = page_params()


def configure_pagination(page_config: Any) -> None:
    """Bind list endpoints to the app's PAGE__ settings."""

    global _resolve
    _resolve = page_params(PaginationSettings.from_object(page_config))


def get_page_params(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int | None, Query(ge=1, description="Items per page")] = None,
) -> PageParams:
    return _resolve(page=page, page_size=page_size)
