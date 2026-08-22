from backend_toolkit_pagination import Page, PageParams
from fastapi import UploadFile

from backend_toolkit_storage import (
    Storage,
    StorageObjectNotFoundError,
    delete_attachments_for,
    store_attachment,
)

from app.exceptions import AttachmentNotFoundError, NoteNotFoundError
from app.models import Attachment, Note
from app.services.unit_of_work import UnitOfWorkBase


class NoteService:
    def __init__(self, uow: UnitOfWorkBase, storage: Storage) -> None:
        self.uow = uow
        self.storage = storage

    async def list_notes(self, params: PageParams) -> Page[Note]:
        return await self.uow.notes.list_page(params)

    async def get_note(self, note_id: int) -> Note:
        note = await self.uow.notes.get_by_id(note_id)
        if note is None:
            raise NoteNotFoundError(note_id)
        return note

    async def create_note(
        self,
        title: str,
        body: str,
        cover: UploadFile | None = None,
        files: list[UploadFile] | None = None,
    ) -> Note:
        note = await self.uow.notes.add(Note(title=title, body=body))
        if cover is not None and cover.filename:
            await self._store_upload(note, "cover", cover)
        for upload in files or []:
            if upload.filename:
                await self._store_upload(note, "files", upload)
        await self.uow.commit()
        return await self._reload(note.id)

    async def delete_note(self, note_id: int) -> None:
        note = await self.get_note(note_id)
        await self.uow.notes.delete(note.id)
        await self.uow.commit()

    async def replace_cover(self, note_id: int, cover: UploadFile) -> Note:
        note = await self.get_note(note_id)
        await delete_attachments_for(self.uow.session, note, field_name="cover")
        await self._store_upload(note, "cover", cover)
        await self.uow.commit()
        return await self._reload(note.id)

    async def add_files(self, note_id: int, files: list[UploadFile]) -> Note:
        note = await self.get_note(note_id)
        for upload in files:
            if upload.filename:
                await self._store_upload(note, "files", upload)
        await self.uow.commit()
        return await self._reload(note.id)

    async def get_attachment(self, note_id: int, attachment_id: int) -> Attachment:
        note = await self.get_note(note_id)
        attachment = await self.uow.attachments.get_by_id(attachment_id)
        if (
            attachment is None
            or attachment.parent_table != note.__tablename__
            or attachment.parent_id != note.id
        ):
            raise AttachmentNotFoundError(attachment_id)
        return attachment

    async def download_attachment(
        self,
        note_id: int,
        attachment_id: int,
    ) -> tuple[Attachment, bytes]:
        attachment = await self.get_attachment(note_id, attachment_id)
        try:
            stored = await self.storage.get(attachment.key)
        except StorageObjectNotFoundError as exc:
            raise AttachmentNotFoundError(attachment_id) from exc
        return attachment, stored.content

    async def delete_attachment(self, note_id: int, attachment_id: int) -> Note:
        attachment = await self.get_attachment(note_id, attachment_id)
        await self.uow.session.delete(attachment)
        await self.uow.commit()
        return await self._reload(note_id)

    async def _reload(self, note_id: int) -> Note:
        self.uow.session.expire_all()
        return await self.get_note(note_id)

    async def _store_upload(
        self,
        note: Note,
        field_name: str,
        upload: UploadFile,
    ) -> Attachment:
        return await store_attachment(
            self.storage,
            parent=note,
            field_name=field_name,
            data=await upload.read(),
            filename=upload.filename or "attachment",
            content_type=upload.content_type,
        )
