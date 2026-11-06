from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.errors import ConflictError, NotFoundError
from app.core.security import Principal
from app.models import PricingAudit, PricingRecord
from app.repositories.pricing import PricingRepository
from app.schemas.common import Page
from app.schemas.pricing import PricingRecordRead, PricingRecordUpdate, PricingSearchParams

_EDITABLE_FIELDS = ("product_name", "price")


class PricingService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._records = PricingRepository(session)

    def search(self, params: PricingSearchParams) -> Page[PricingRecordRead]:
        records, total = self._records.search(params)
        return Page[PricingRecordRead](
            items=[PricingRecordRead.model_validate(record) for record in records],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    def get(self, record_id: int) -> PricingRecord:
        if record := self._records.get(record_id):
            return record
        raise NotFoundError(f"Pricing record {record_id} not found")

    def update(
        self, record_id: int, payload: PricingRecordUpdate, principal: Principal
    ) -> PricingRecord:
        record = self.get(record_id)
        if record.version != payload.version:
            raise _version_conflict(record_id)

        changes = _apply_changes(record, payload)
        if not changes:
            return record

        record.updated_by = principal.subject
        try:
            self._session.flush()
            self._records.add_audit(
                PricingAudit(
                    record_id=record.id,
                    version=record.version,
                    changes=changes,
                    changed_by=principal.subject,
                )
            )
            self._session.commit()
        except StaleDataError as exc:
            self._session.rollback()
            raise _version_conflict(record_id) from exc

        self._session.refresh(record)
        return record

    def history(self, record_id: int) -> Sequence[PricingAudit]:
        if not self._records.exists(record_id):
            raise NotFoundError(f"Pricing record {record_id} not found")
        return self._records.history(record_id)


def _apply_changes(record: PricingRecord, payload: PricingRecordUpdate) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    for name in _EDITABLE_FIELDS:
        new_value = getattr(payload, name)
        old_value = getattr(record, name)
        if new_value is None or new_value == old_value:
            continue
        changes[name] = {"old": str(old_value), "new": str(new_value)}
        setattr(record, name, new_value)
    return changes


def _version_conflict(record_id: int) -> ConflictError:
    return ConflictError(
        f"Pricing record {record_id} was modified by another user. Reload and try again."
    )
