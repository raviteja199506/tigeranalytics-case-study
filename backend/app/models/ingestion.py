from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BigIntPrimaryKey


class IngestionStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        Index("ix_ingestion_jobs_checksum", "checksum"),
        Index("ix_ingestion_jobs_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))
    checksum: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(
            IngestionStatus,
            native_enum=False,
            length=32,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=IngestionStatus.PENDING,
    )
    total_rows: Mapped[int] = mapped_column(default=0)
    accepted_rows: Mapped[int] = mapped_column(default=0)
    rejected_rows: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    errors: Mapped[list["IngestionError"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", passive_deletes=True
    )


class IngestionError(Base):
    __tablename__ = "ingestion_errors"
    __table_args__ = (Index("ix_ingestion_errors_job_row", "job_id", "row_number"),)

    id: Mapped[int] = mapped_column(BigIntPrimaryKey, primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("ingestion_jobs.id", ondelete="CASCADE"))
    row_number: Mapped[int]
    message: Mapped[str] = mapped_column(Text)
    raw_line: Mapped[str | None] = mapped_column(Text)

    job: Mapped[IngestionJob] = relationship(back_populates="errors")
