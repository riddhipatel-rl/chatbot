from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector"
    )

    op.create_table(
        "documents",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "source_file",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "file_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "file_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_hash"),
    )

    op.create_index(
        "ix_documents_file_hash",
        "documents",
        ["file_hash"],
    )

    op.create_table(
        "chunks",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "text",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "locations",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "element_types",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "embedding",
            Vector(384),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_chunks_document_id",
        "chunks",
        ["document_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_chunks_document_id",
        table_name="chunks",
    )

    op.drop_table("chunks")

    op.drop_index(
        "ix_documents_file_hash",
        table_name="documents",
    )

    op.drop_table("documents")

    op.execute(
        "DROP EXTENSION IF EXISTS vector"
    )