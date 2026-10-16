from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func, Integer, Boolean, UniqueConstraint, Index, text

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


EMBEDDING_DIMENSION = 384


class Document(Base):
    __tablename__ = "documents"

    __table_args__ = (
        UniqueConstraint(
            "logical_document_id",
            "file_hash",
            name="uq_documents_logical_document_hash",
        ),
        Index(
            "ix_documents_source_file_latest",
            "source_file",
            "is_latest",
        ),
        Index(
            "uq_documents_one_latest_per_logical_document",
            "logical_document_id",
            unique=True,
            postgresql_where=text("is_latest IS TRUE"),
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    source_file: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    logical_document_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_latest: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
    )

    locations: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    element_types: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSION),
        nullable=True,
    )

    document: Mapped["Document"] = relationship(
        back_populates="chunks",
    )