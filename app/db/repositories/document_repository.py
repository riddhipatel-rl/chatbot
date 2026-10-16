
from sqlalchemy import select, update, func
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
        logical_document_id: str | None = None,
        version_number: int = 1,
        is_latest: bool = True,
    ) -> Document:
        document = Document(
            id=document_id,
            source_file=source_file,
            file_type=file_type,
            file_hash=file_hash,
            logical_document_id=logical_document_id or document_id,
            version_number=version_number,
            is_latest=is_latest,
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
            .where(
                Document.source_file == source_file,
                Document.is_latest.is_(True),
            )
            .order_by(Document.created_at.desc())
        )
        return self.session.scalars(statement).first()
    

    def get_by_hash_for_logical_document(
        self,
        logical_document_id: str,
        file_hash: str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.logical_document_id == logical_document_id,
            Document.file_hash == file_hash,
        )
        return self.session.scalars(statement).first()

    def activate_version(
        self,
        logical_document_id: str,
        document_id: str,
    ) -> bool:
        document = self.get_by_id(document_id)

        if (
            document is None
            or document.logical_document_id != logical_document_id
        ):
            return False

        self.session.execute(
            update(Document)
            .where(
                Document.logical_document_id == logical_document_id
            )
            .values(is_latest=False)
        )

        self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(is_latest=True)
        )

        self.session.flush()
        return True

    def get_next_version_number(
        self,
        logical_document_id: str,
    ) -> int:
        statement = select(
            func.max(Document.version_number)
        ).where(
            Document.logical_document_id == logical_document_id
        )

        current_max = self.session.scalar(statement)
        return (current_max or 0) + 1

    def mark_versions_not_latest(
        self,
        logical_document_id: str,
    ) -> None:
        self.session.execute(
            update(Document)
            .where(
                Document.logical_document_id == logical_document_id,
                Document.is_latest.is_(True),
            )
            .values(is_latest=False)
        )

        self.session.flush()
