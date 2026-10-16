
from dataclasses import asdict, is_dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document, EMBEDDING_DIMENSION
from app.ingestion.models import DocumentChunk, SourceLocation


class ChunkRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        chunk: DocumentChunk,
        embedding: list[float] | None = None,
    ) -> Chunk:
        if embedding is not None and len(embedding) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSION} embedding dimensions, "
                f"received {len(embedding)}"
            )

        locations = [
            asdict(location) if is_dataclass(location) else location
            for location in chunk.locations
        ]

        db_chunk = Chunk(
            id=chunk.chunk_id,
            document_id=chunk.document_id,
            text=chunk.text,
            metadata_=chunk.metadata,
            locations=locations,
            element_types=chunk.element_types,
            embedding=embedding,
        )

        self.session.add(db_chunk)
        self.session.flush()
        return db_chunk

    def get_by_id(self, chunk_id: str) -> Chunk | None:
        return self.session.get(Chunk, chunk_id)

    def get_by_document_id(self, document_id: str) -> list[Chunk]:
        statement = (
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.id)
        )
        return list(self.session.scalars(statement).all())

    def get_latest_document_chunks(self) -> list[DocumentChunk]:
        statement = (
            select(Chunk, Document.source_file)
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.is_latest.is_(True))
            .order_by(Document.source_file, Chunk.id)
        )

        rows = self.session.execute(statement).all()

        return [
            DocumentChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                text=chunk.text,
                source_file=source_file,
                locations=[
                    SourceLocation(**location)
                    if isinstance(location, dict)
                    else location
                    for location in (chunk.locations or [])
                ],
                element_types=chunk.element_types or [],
                metadata=chunk.metadata_ or {},
            )
            for chunk, source_file in rows
        ]

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[tuple[Chunk, float]]:
        if len(query_embedding) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSION} embedding dimensions, "
                f"received {len(query_embedding)}"
            )

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        distance = Chunk.embedding.cosine_distance(query_embedding)

        statement = (
            select(Chunk, distance.label("distance"))
            .where(Chunk.embedding.is_not(None))
        )

        if document_id is not None:
            statement = statement.where(
                Chunk.document_id == document_id
            )

        statement = statement.order_by(distance).limit(top_k)

        rows = self.session.execute(statement).all()

        return [
            (chunk, float(distance_value))
            for chunk, distance_value in rows
        ]
