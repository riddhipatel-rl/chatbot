
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        document_id: str,
        source_file: str,
        file_type: str,
        file_hash: str,
    ) -> Document:
        document = Document(
            id=document_id,
            source_file=source_file,
            file_type=file_type,
            file_hash=file_hash,
        )
        self.session.add(document)
        self.session.flush()
        return document

    def get_by_id(self, document_id: str) -> Document | None:
        return self.session.get(Document, document_id)

    def get_by_hash(self, file_hash: str) -> Document | None:
        statement = select(Document).where(
            Document.file_hash == file_hash
        )
        return self.session.scalars(statement).first()

    def delete(self, document_id: str) -> bool:
        document = self.get_by_id(document_id)

        if document is None:
            return False

        self.session.delete(document)
        self.session.flush()
        return True

    def get_by_source_file(
        self,
        source_file: str,
    ) -> Document | None:
        statement = (
            select(Document)
            .where(Document.source_file == source_file)
            .order_by(Document.created_at.desc())
        )
        return self.session.scalars(statement).first()
