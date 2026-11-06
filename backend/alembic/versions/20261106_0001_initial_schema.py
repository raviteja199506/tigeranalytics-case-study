"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BIGINT_PK = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
TIMESTAMP = sa.DateTime(timezone=True)
JSON_DOCUMENT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("uploaded_by", sa.String(128), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", TIMESTAMP),
        sa.Column("completed_at", TIMESTAMP),
    )
    op.create_index("ix_ingestion_jobs_checksum", "ingestion_jobs", ["checksum"])
    op.create_index("ix_ingestion_jobs_created_at", "ingestion_jobs", ["created_at"])

    op.create_table(
        "ingestion_errors",
        sa.Column("id", BIGINT_PK, primary_key=True, autoincrement=True),
        sa.Column(
            "job_id",
            sa.String(36),
            sa.ForeignKey("ingestion_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_line", sa.Text()),
    )
    op.create_index("ix_ingestion_errors_job_row", "ingestion_errors", ["job_id", "row_number"])

    op.create_table(
        "pricing_records",
        sa.Column("id", BIGINT_PK, primary_key=True, autoincrement=True),
        sa.Column("store_id", sa.String(32), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("price", sa.Numeric(14, 4), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "source_job_id",
            sa.String(36),
            sa.ForeignKey("ingestion_jobs.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.String(128)),
        sa.UniqueConstraint(
            "store_id", "sku", "price_date", name="uq_pricing_records_store_sku_date"
        ),
        sa.CheckConstraint("price > 0", name="ck_pricing_records_price_positive"),
    )
    op.create_index("ix_pricing_records_store_date", "pricing_records", ["store_id", "price_date"])
    op.create_index("ix_pricing_records_sku_date", "pricing_records", ["sku", "price_date"])
    op.create_index("ix_pricing_records_price_date", "pricing_records", ["price_date"])

    op.create_table(
        "pricing_audit",
        sa.Column("id", BIGINT_PK, primary_key=True, autoincrement=True),
        sa.Column(
            "record_id",
            BIGINT_PK,
            sa.ForeignKey("pricing_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("changes", JSON_DOCUMENT, nullable=False),
        sa.Column("changed_by", sa.String(128), nullable=False),
        sa.Column("changed_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pricing_audit_record_changed", "pricing_audit", ["record_id", "changed_at"])

    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute(
            "CREATE INDEX ix_pricing_records_product_name_trgm "
            "ON pricing_records USING gin (product_name gin_trgm_ops)"
        )


def downgrade() -> None:
    op.drop_table("pricing_audit")
    op.drop_table("pricing_records")
    op.drop_table("ingestion_errors")
    op.drop_table("ingestion_jobs")
