from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from sqlalchemy import ColumnElement, Insert, UnaryExpression, func, or_, select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.models import PricingAudit, PricingRecord
from app.schemas.pricing import PricingSearchParams

_SORT_COLUMNS: dict[str, InstrumentedAttribute[Any]] = {
    "store_id": PricingRecord.store_id,
    "sku": PricingRecord.sku,
    "product_name": PricingRecord.product_name,
    "price": PricingRecord.price,
    "price_date": PricingRecord.price_date,
    "updated_at": PricingRecord.updated_at,
}

_UPSERT_DIALECTS = {"postgresql": postgresql.insert, "sqlite": sqlite.insert}


class PricingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, record_id: int) -> PricingRecord | None:
        return self._session.get(PricingRecord, record_id)

    def exists(self, record_id: int) -> bool:
        stmt = select(PricingRecord.id).where(PricingRecord.id == record_id)
        return self._session.scalar(stmt) is not None

    def search(self, params: PricingSearchParams) -> tuple[Sequence[PricingRecord], int]:
        filters = list(_filters(params))
        total = self._session.scalar(
            select(func.count()).select_from(PricingRecord).where(*filters)
        )
        stmt = (
            select(PricingRecord)
            .where(*filters)
            .order_by(_ordering(params.sort), PricingRecord.id)
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
        )
        return self._session.scalars(stmt).all(), total or 0

    def upsert_many(self, rows: Sequence[Mapping[str, Any]]) -> None:
        if rows:
            self._session.execute(self._upsert_statement(), rows)

    def add_audit(self, entry: PricingAudit) -> None:
        self._session.add(entry)

    def history(self, record_id: int) -> Sequence[PricingAudit]:
        stmt = (
            select(PricingAudit)
            .where(PricingAudit.record_id == record_id)
            .order_by(PricingAudit.changed_at.desc(), PricingAudit.id.desc())
        )
        return self._session.scalars(stmt).all()

    def _upsert_statement(self) -> Insert:
        table = PricingRecord.__table__
        insert = _UPSERT_DIALECTS[self._session.get_bind().dialect.name]
        stmt = insert(table)
        return stmt.on_conflict_do_update(
            index_elements=[table.c.store_id, table.c.sku, table.c.price_date],
            set_={
                "product_name": stmt.excluded.product_name,
                "price": stmt.excluded.price,
                "source_job_id": stmt.excluded.source_job_id,
                "updated_by": stmt.excluded.updated_by,
                "updated_at": func.now(),
                "version": table.c.version + 1,
            },
            where=or_(
                table.c.price != stmt.excluded.price,
                table.c.product_name != stmt.excluded.product_name,
            ),
        )


def _filters(params: PricingSearchParams) -> Iterator[ColumnElement[bool]]:
    if params.store_id:
        yield PricingRecord.store_id == params.store_id
    if params.sku:
        yield PricingRecord.sku == params.sku
    if params.product_name:
        yield PricingRecord.product_name.icontains(params.product_name, autoescape=True)
    if params.min_price is not None:
        yield PricingRecord.price >= params.min_price
    if params.max_price is not None:
        yield PricingRecord.price <= params.max_price
    if params.date_from:
        yield PricingRecord.price_date >= params.date_from
    if params.date_to:
        yield PricingRecord.price_date <= params.date_to


def _ordering(sort: str) -> UnaryExpression[Any]:
    column = _SORT_COLUMNS[sort.removeprefix("-")]
    return column.desc() if sort.startswith("-") else column.asc()
