from collections.abc import Sequence

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.models import IngestionError, IngestionJob, IngestionStatus
from app.services.csv_parser import RowError


class IngestionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, job: IngestionJob) -> None:
        self._session.add(job)

    def get(self, job_id: str) -> IngestionJob | None:
        return self._session.get(IngestionJob, job_id)

    def find_by_checksum(self, checksum: str) -> IngestionJob | None:
        stmt = (
            select(IngestionJob)
            .where(
                IngestionJob.checksum == checksum,
                IngestionJob.status != IngestionStatus.FAILED,
            )
            .limit(1)
        )
        return self._session.scalar(stmt)

    def list_recent(self, limit: int) -> Sequence[IngestionJob]:
        stmt = select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit)
        return self._session.scalars(stmt).all()

    def add_errors(self, job_id: str, errors: Sequence[RowError]) -> None:
        if not errors:
            return
        self._session.execute(
            insert(IngestionError),
            [
                {
                    "job_id": job_id,
                    "row_number": error.row_number,
                    "message": error.message,
                    "raw_line": error.raw_line,
                }
                for error in errors
            ],
        )

    def list_errors(self, job_id: str, limit: int) -> Sequence[IngestionError]:
        stmt = (
            select(IngestionError)
            .where(IngestionError.job_id == job_id)
            .order_by(IngestionError.row_number)
            .limit(limit)
        )
        return self._session.scalars(stmt).all()
