from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.pricing import PRICE_PRECISION, PRICE_SCALE

SORTABLE_FIELDS = ("store_id", "sku", "product_name", "price", "price_date", "updated_at")
SORT_PATTERN = rf"^-?({'|'.join(SORTABLE_FIELDS)})$"


class PricingSearchParams(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    store_id: str | None = Field(default=None, max_length=32)
    sku: str | None = Field(default=None, max_length=64)
    product_name: str | None = Field(default=None, max_length=255)
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    date_from: date | None = None
    date_to: date | None = None
    sort: str = Field(default="-price_date", pattern=SORT_PATTERN)
    page: int = Field(default=1, ge=1, le=10_000)
    page_size: int = Field(default=25, ge=1, le=200)

    @model_validator(mode="after")
    def validate_ranges(self) -> Self:
        prices = (self.min_price, self.max_price)
        if None not in prices and prices[0] > prices[1]:
            raise ValueError("min_price must be less than or equal to max_price")
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        return self


class PricingRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store_id: str
    sku: str
    product_name: str
    price: Decimal
    price_date: date
    version: int
    source_job_id: str | None
    created_at: datetime
    updated_at: datetime
    updated_by: str | None


class PricingRecordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    price: Decimal | None = Field(
        default=None, gt=0, max_digits=PRICE_PRECISION, decimal_places=PRICE_SCALE
    )
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def require_change(self) -> Self:
        if self.product_name is None and self.price is None:
            raise ValueError("At least one of product_name or price must be provided")
        return self


class FieldChange(BaseModel):
    old: str | None
    new: str | None


class PricingAuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int
    changes: dict[str, FieldChange]
    changed_by: str
    changed_at: datetime
