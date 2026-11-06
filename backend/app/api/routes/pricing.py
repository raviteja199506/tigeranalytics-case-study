from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import EditorDep, PricingServiceDep, ViewerDep
from app.schemas.common import Page
from app.schemas.pricing import (
    PricingAuditRead,
    PricingRecordRead,
    PricingRecordUpdate,
    PricingSearchParams,
)

router = APIRouter(prefix="/pricing-records", tags=["pricing-records"])


@router.get("", response_model=Page[PricingRecordRead])
def search_pricing_records(
    params: Annotated[PricingSearchParams, Query()],
    service: PricingServiceDep,
    _: ViewerDep,
) -> Page[PricingRecordRead]:
    return service.search(params)


@router.get("/{record_id}", response_model=PricingRecordRead)
def get_pricing_record(
    record_id: int, service: PricingServiceDep, _: ViewerDep
) -> PricingRecordRead:
    return PricingRecordRead.model_validate(service.get(record_id))


@router.patch("/{record_id}", response_model=PricingRecordRead)
def update_pricing_record(
    record_id: int,
    payload: PricingRecordUpdate,
    service: PricingServiceDep,
    principal: EditorDep,
) -> PricingRecordRead:
    return PricingRecordRead.model_validate(service.update(record_id, payload, principal))


@router.get("/{record_id}/history", response_model=list[PricingAuditRead])
def get_pricing_record_history(
    record_id: int, service: PricingServiceDep, _: ViewerDep
) -> list[PricingAuditRead]:
    return [PricingAuditRead.model_validate(entry) for entry in service.history(record_id)]
