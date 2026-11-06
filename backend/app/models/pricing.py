from datetime import date, datetime
from decimal import Decimal
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BigIntPrimaryKey

PRICE_PRECISION = 14
PRICE_SCALE = 4


class PricingRecord(Base):
    __tablename__ = "pricing_records"
    __table_args__ = (
        UniqueConstraint("store_id", "sku", "price_date", name="uq_pricing_records_store_sku_date"),
        CheckConstraint("price > 0", name="ck_pricing_records_price_positive"),
        Index("ix_pricing_records_store_date", "store_id", "price_date"),
        Index("ix_pricing_records_sku_date", "sku", "price_date"),
        Index("ix_pricing_records_price_date", "price_date"),
    )

    id: Mapped[int] = mapped_column(BigIntPrimaryKey, primary_key=True)
    store_id: Mapped[str] = mapped_column(String(32))
    sku: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(PRICE_PRECISION, PRICE_SCALE))
    price_date: Mapped[date] = mapped_column(Date)
    version: Mapped[int] = mapped_column(default=1)
    source_job_id: Mapped[str | None] = mapped_column(
        ForeignKey("ingestion_jobs.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[str | None] = mapped_column(String(128))

    __mapper_args__: ClassVar[dict[str, Any]] = {"version_id_col": version}


class PricingAudit(Base):
    __tablename__ = "pricing_audit"
    __table_args__ = (Index("ix_pricing_audit_record_changed", "record_id", "changed_at"),)

    id: Mapped[int] = mapped_column(BigIntPrimaryKey, primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("pricing_records.id", ondelete="CASCADE"))
    version: Mapped[int]
    changes: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    changed_by: Mapped[str] = mapped_column(String(128))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
