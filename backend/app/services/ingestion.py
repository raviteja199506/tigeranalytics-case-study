import io
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import PurePath
from typing import Any, BinaryIO

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ConflictError, InvalidInputError, NotFoundError
from app.db.database import Database
from app.infrastructure.storage import FileStorage
from app.models import IngestionError, IngestionJob, IngestionStatus
from app.models.base import utcnow
from app.repositories.ingestion import IngestionRepository
from app.repositories.pricing import PricingRepository
from app.services.csv_parser import CsvFormatError, PricingRow, RowError, parse_pricing_csv

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = frozenset({".csv"})


class IngestionService:
    def __init__(self, session: Session, storage: FileStorage, settings: Settings) -> None:
        self._session = session
        self._storage = storage
        self._settings = settings
        self._jobs = IngestionRepository(session)

    def submit(self, source: BinaryIO, filename: str, uploaded_by: str) -> IngestionJob:
        safe_name = PurePath(filename).name[:255]
        if PurePath(safe_name).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise InvalidInputError("Only .csv files are accepted")

        stored = self._storage.save(source, max_bytes=self._settings.max_upload_bytes)
        if stored.size_bytes == 0:
            self._storage.delete(stored.key)
            raise InvalidInputError("Uploaded file is empty")

        if duplicate := self._jobs.find_by_checksum(stored.checksum):
            self._storage.delete(stored.key)
            raise ConflictError(
                f"An identical file was already uploaded as '{duplicate.filename}' "
                f"(job {duplicate.id})"
            )

        job = IngestionJob(
            filename=safe_name,
            storage_key=stored.key,
            checksum=stored.checksum,
            size_bytes=stored.size_bytes,
            uploaded_by=uploaded_by,
        )
        self._jobs.add(job)
        self._session.commit()
        logger.info("Ingestion job submitted", extra={"job_id": job.id, "bytes": job.size_bytes})
        return job

    def get(self, job_id: str) -> IngestionJob:
        if job := self._jobs.get(job_id):
            return job
        raise NotFoundError(f"Ingestion job {job_id} not found")

    def list_recent(self, limit: int) -> Sequence[IngestionJob]:
        return self._jobs.list_recent(limit)

    def list_errors(self, job_id: str, limit: int) -> Sequence[IngestionError]:
        self.get(job_id)
        return self._jobs.list_errors(job_id, limit)


@dataclass
class _Progress:
    total: int = 0
    accepted: int = 0
    rejected: int = 0
    batch: dict[tuple[str, str, date], dict[str, Any]] = field(default_factory=dict)
    errors: list[RowError] = field(default_factory=list)
    reported_errors: int = 0


class IngestionProcessor:
    def __init__(self, session: Session, storage: FileStorage, settings: Settings) -> None:
        self._session = session
        self._storage = storage
        self._settings = settings
        self._jobs = IngestionRepository(session)
        self._pricing = PricingRepository(session)

    def run(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job is None or job.status is not IngestionStatus.PENDING:
            logger.warning("Skipping ingestion job", extra={"job_id": job_id})
            return

        job.status = IngestionStatus.PROCESSING
        job.started_at = utcnow()
        self._session.commit()

        try:
            self._ingest(job)
        except CsvFormatError as exc:
            self._fail(job, str(exc))
        except UnicodeDecodeError:
            self._fail(job, "File must be UTF-8 encoded")
        except Exception:
            logger.exception("Ingestion job crashed", extra={"job_id": job_id})
            self._fail(job, "Unexpected error while processing the file")

    def _ingest(self, job: IngestionJob) -> None:
        progress = _Progress()
        with (
            self._storage.open(job.storage_key) as binary,
            io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as text,
        ):
            for result in parse_pricing_csv(text):
                progress.total += 1
                if isinstance(result, RowError):
                    self._record_error(progress, result)
                else:
                    self._stage_row(progress, result, job)
                if len(progress.batch) >= self._settings.ingestion_batch_size:
                    self._flush(job, progress)

        self._flush(job, progress)
        self._complete(job, progress)

    def _stage_row(self, progress: _Progress, row: PricingRow, job: IngestionJob) -> None:
        progress.accepted += 1
        progress.batch[(row.store_id, row.sku, row.price_date)] = {
            **row.model_dump(),
            "source_job_id": job.id,
            "updated_by": job.uploaded_by,
        }

    def _record_error(self, progress: _Progress, error: RowError) -> None:
        progress.rejected += 1
        if progress.reported_errors < self._settings.max_reported_errors:
            progress.errors.append(error)
            progress.reported_errors += 1

    def _flush(self, job: IngestionJob, progress: _Progress) -> None:
        self._pricing.upsert_many(list(progress.batch.values()))
        self._jobs.add_errors(job.id, progress.errors)
        job.total_rows = progress.total
        job.accepted_rows = progress.accepted
        job.rejected_rows = progress.rejected
        self._session.commit()
        progress.batch.clear()
        progress.errors.clear()

    def _complete(self, job: IngestionJob, progress: _Progress) -> None:
        if progress.total == 0:
            self._fail(job, "File contains a header but no data rows")
            return
        if progress.accepted == 0:
            self._fail(job, "No valid rows found; see row errors for details")
            return

        has_errors = progress.rejected > 0
        job.status = (
            IngestionStatus.COMPLETED_WITH_ERRORS if has_errors else IngestionStatus.COMPLETED
        )
        job.completed_at = utcnow()
        self._session.commit()
        logger.info(
            "Ingestion job completed",
            extra={
                "job_id": job.id,
                "total_rows": progress.total,
                "accepted_rows": progress.accepted,
                "rejected_rows": progress.rejected,
            },
        )

    def _fail(self, job: IngestionJob, message: str) -> None:
        self._session.rollback()
        job.status = IngestionStatus.FAILED
        job.error_message = message
        job.completed_at = utcnow()
        self._session.commit()
        logger.warning("Ingestion job failed", extra={"job_id": job.id, "reason": message})


def run_ingestion(
    job_id: str, database: Database, storage: FileStorage, settings: Settings
) -> None:
    with database.session() as session:
        IngestionProcessor(session, storage, settings).run(job_id)
