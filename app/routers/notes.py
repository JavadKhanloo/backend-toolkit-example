from typing import Annotated

from backend_toolkit_auth import CurrentUser, get_current_user, require_roles
from backend_toolkit_logger import get_logger
from backend_toolkit_pagination import Page, PageParams, get_page_params
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from starlette.responses import Response

from app.dependencies import get_note_service
from app.exceptions import AttachmentNotFoundError, NoteNotFoundError
from app.schemas import NoteRead
from app.services import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])
logger = get_logger(__name__)
require_admin = require_roles("admin")


def _http_error(exc: NoteNotFoundError | AttachmentNotFoundError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


@router.post("", response_model=NoteRead)
async def create_note(
    title: Annotated[str, Form()],
    body: Annotated[str, Form()],
    cover: Annotated[UploadFile | None, File()] = None,
    files: Annotated[
        list[UploadFile],
        File(
            json_schema_extra={
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "binary",
                    "contentMediaType": "application/octet-stream",
                },
            },
        ),
    ] = [],
    service: NoteService = Depends(get_note_service),
    user: CurrentUser = Depends(get_current_user),
) -> NoteRead:
    note = await service.create_note(
        title=title,
        body=body,
        cover=cover,
        files=files,
    )
    logger.info("note_created", note_id=note.id, title=note.title, user=user.username)
    return NoteRead.model_validate(note)


@router.get("", response_model=Page[NoteRead])
async def list_notes(
    params: PageParams = Depends(get_page_params),
    service: NoteService = Depends(get_note_service),
    user: CurrentUser = Depends(get_current_user),
) -> Page[NoteRead]:
    page = await service.list_notes(params)
    logger.info("notes_listed", count=page.total, user=user.username)
    return page.map(NoteRead.model_validate)


@router.get("/{note_id}", response_model=NoteRead)
async def read_note(
    note_id: int,
    service: NoteService = Depends(get_note_service),
    user: CurrentUser = Depends(get_current_user),
) -> NoteRead:
    try:
        note = await service.get_note(note_id)
    except NoteNotFoundError as exc:
        raise _http_error(exc) from exc
    return NoteRead.model_validate(note)


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    service: NoteService = Depends(get_note_service),
    user: CurrentUser = Depends(require_admin),
) -> None:
    try:
        await service.delete_note(note_id)
    except NoteNotFoundError as exc:
        raise _http_error(exc) from exc
    logger.info("note_deleted", note_id=note_id, user=user.username)


@router.post("/{note_id}/cover", response_model=NoteRead)
async def replace_cover(
    note_id: int,
    cover: UploadFile = File(...),
    service: NoteService = Depends(get_note_service),
    user: CurrentUser = Depends(get_current_user),
) -> NoteRead:
    try:
        note = await service.replace_cover(note_id, cover)
    except NoteNotFoundError as exc:
        raise _http_error(exc) from exc
    logger.info("note_cover_replaced", note_id=note_id, user=user.username)
    return NoteRead.model_validate(note)


@router.post("/{note_id}/files", response_model=NoteRead)
async def add_files(
    note_id: int,
    files: Annotated[
        list[UploadFile],
        File(
            json_schema_extra={
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "binary",
                    "contentMediaType": "application/octet-stream",
                },
            },
        ),
    ],
    service: NoteService = Depends(get_note_service),
    user: CurrentUser = Depends(get_current_user),
) -> NoteRead:
    try:
        note = await service.add_files(note_id, files)
    except NoteNotFoundError as exc:
        raise _http_error(exc) from exc
    logger.info("note_files_added", note_id=note_id, count=len(files), user=user.username)
    return NoteRead.model_validate(note)


@router.get("/{note_id}/attachments/{attachment_id}")
async def download_attachment(
    note_id: int,
    attachment_id: int,
    service: NoteService = Depends(get_note_service),
    user: CurrentUser = Depends(get_current_user),
) -> Response:
    try:
        attachment, content = await service.download_attachment(
            note_id,
            attachment_id,
        )
    except (NoteNotFoundError, AttachmentNotFoundError) as exc:
        raise _http_error(exc) from exc

    return Response(
        content=content,
        media_type=attachment.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"',
        },
    )


@router.delete("/{note_id}/attachments/{attachment_id}", response_model=NoteRead)
async def delete_attachment(
    note_id: int,
    attachment_id: int,
    service: NoteService = Depends(get_note_service),
    user: CurrentUser = Depends(require_admin),
) -> NoteRead:
    try:
        note = await service.delete_attachment(note_id, attachment_id)
    except (NoteNotFoundError, AttachmentNotFoundError) as exc:
        raise _http_error(exc) from exc
    logger.info(
        "note_attachment_deleted",
        note_id=note_id,
        attachment_id=attachment_id,
        user=user.username,
    )
    return NoteRead.model_validate(note)
