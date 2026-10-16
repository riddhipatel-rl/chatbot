from alembic import op
import sqlalchemy as sa


revision = "002_document_versioning"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "logical_document_id",
            sa.String(length=36),
            nullable=True,
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "is_latest",
            sa.Boolean(),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    documents = sa.table(
        "documents",
        sa.column("id", sa.String(length=36)),
        sa.column("source_file", sa.String(length=500)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("logical_document_id", sa.String(length=36)),
        sa.column("version_number", sa.Integer()),
        sa.column("is_latest", sa.Boolean()),
    )

    rows = connection.execute(
        sa.select(
            documents.c.id,
            documents.c.source_file,
            documents.c.created_at,
        ).order_by(
            documents.c.source_file,
            documents.c.created_at,
            documents.c.id,
        )
    ).mappings().all()

    logical_ids = {}
    version_counts = {}
    latest_ids = {}

    for row in rows:
        source_file = row["source_file"]
        document_id = row["id"]

        if source_file not in logical_ids:
            logical_ids[source_file] = document_id
            version_counts[source_file] = 0

        version_counts[source_file] += 1

        connection.execute(
            documents.update()
            .where(documents.c.id == document_id)
            .values(
                logical_document_id=logical_ids[source_file],
                version_number=version_counts[source_file],
                is_latest=False,
            )
        )

        latest_ids[source_file] = document_id

    for document_id in latest_ids.values():
        connection.execute(
            documents.update()
            .where(documents.c.id == document_id)
            .values(is_latest=True)
        )

    op.alter_column(
        "documents",
        "logical_document_id",
        existing_type=sa.String(length=36),
        nullable=False,
    )
    op.alter_column(
        "documents",
        "version_number",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "documents",
        "is_latest",
        existing_type=sa.Boolean(),
        nullable=False,
    )

    op.drop_constraint(
        "documents_file_hash_key",
        "documents",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_documents_logical_document_hash",
        "documents",
        ["logical_document_id", "file_hash"],
    )

    op.create_index(
        "ix_documents_logical_document_id",
        "documents",
        ["logical_document_id"],
    )

    op.create_index(
        "ix_documents_source_file_latest",
        "documents",
        ["source_file", "is_latest"],
    )

    op.create_index(
        "uq_documents_one_latest_per_logical_document",
        "documents",
        ["logical_document_id"],
        unique=True,
        postgresql_where=sa.text("is_latest IS TRUE"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_documents_one_latest_per_logical_document",
        table_name="documents",
    )
    op.drop_index(
        "ix_documents_source_file_latest",
        table_name="documents",
    )
    op.drop_index(
        "ix_documents_logical_document_id",
        table_name="documents",
    )

    op.drop_constraint(
        "uq_documents_logical_document_hash",
        "documents",
        type_="unique",
    )

    op.create_unique_constraint(
        "documents_file_hash_key",
        "documents",
        ["file_hash"],
    )

    op.drop_column("documents", "is_latest")
    op.drop_column("documents", "version_number")
    op.drop_column("documents", "logical_document_id")