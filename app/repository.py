from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Note


class NoteRepository:
    """
    数据访问层，封装 Note 的 CRUD 操作。
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_notes(self) -> List[Note]:
        stmt = select(Note).order_by(Note.created_at.desc())
        return list(self.session.scalars(stmt))

    def get(self, note_id: int) -> Optional[Note]:
        return self.session.get(Note, note_id)

    def create(
        self,
        title: str,
        content: str,
        color: str,
        image_urls: list[str] | None = None,
    ) -> Note:
        note = Note(
            title=title,
            content=content,
            color=color,
            image_urls=image_urls or [],
        )
        self.session.add(note)
        self.session.commit()
        self.session.refresh(note)
        return note

    def update(
        self,
        note: Note,
        title: str,
        content: str,
        color: str,
        image_urls: list[str],
    ) -> Note:
        note.title = title
        note.content = content
        note.color = color
        note.image_urls = image_urls
        self.session.commit()
        self.session.refresh(note)
        return note

    def delete(self, note: Note) -> None:
        self.session.delete(note)
        self.session.commit()


