import csv
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Final, TextIO

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.models.pricing import PRICE_PRECISION, PRICE_SCALE

DISPLAY_NAMES: Final = {
    "store_id": "Store ID",
    "sku": "SKU",
    "product_name": "Product Name",
    "price": "Price",
    "price_date": "Date",
}

_COLUMN_ALIASES: Final = {
    "storeid": "store_id",
    "sku": "sku",
    "productname": "product_name",
    "price": "price",
    "date": "price_date",
    "pricedate": "price_date",
}

_MAX_RAW_LINE_LENGTH: Final = 1_000
_PATTERN_MESSAGE: Final = "may only contain letters, digits, hyphens and underscores"


class CsvFormatError(ValueError):
    pass


class PricingRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    store_id: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_\-]+$")
    sku: str = Field(min_length=1, max_length=64)
    product_name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(gt=0, max_digits=PRICE_PRECISION, decimal_places=PRICE_SCALE)
    price_date: date

    @field_validator("price_date", mode="before")
    @classmethod
    def parse_iso_date(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("must be a date in YYYY-MM-DD format") from exc


@dataclass(frozen=True, slots=True)
class RowError:
    row_number: int
    message: str
    raw_line: str


def parse_pricing_csv(stream: TextIO) -> Iterator[PricingRow | RowError]:
    reader = csv.reader(stream)
    header = next(reader, None)
    if header is None:
        raise CsvFormatError("File is empty")

    columns = _resolve_columns(header)
    expected_width = len(header)

    for values in reader:
        if not any(value.strip() for value in values):
            continue

        row_number = reader.line_num
        raw_line = ",".join(values)[:_MAX_RAW_LINE_LENGTH]

        if len(values) != expected_width:
            yield RowError(
                row_number, f"Expected {expected_width} columns but found {len(values)}", raw_line
            )
            continue

        try:
            yield PricingRow(**{field: values[index] for field, index in columns.items()})
        except ValidationError as exc:
            yield RowError(row_number, _describe(exc), raw_line)


def _resolve_columns(header: list[str]) -> dict[str, int]:
    columns: dict[str, int] = {}
    for index, name in enumerate(header):
        field = _COLUMN_ALIASES.get(_normalize(name))
        if field is None:
            continue
        if field in columns:
            raise CsvFormatError(f"Duplicate column for {DISPLAY_NAMES[field]}: '{name.strip()}'")
        columns[field] = index

    if missing := DISPLAY_NAMES.keys() - columns.keys():
        names = ", ".join(DISPLAY_NAMES[field] for field in DISPLAY_NAMES if field in missing)
        raise CsvFormatError(f"Missing required columns: {names}")
    return columns


def _normalize(column: str) -> str:
    return re.sub(r"[^a-z0-9]", "", column.strip().lstrip("﻿").lower())


def _describe(error: ValidationError) -> str:
    messages = []
    for detail in error.errors(include_url=False):
        field = str(detail["loc"][0]) if detail["loc"] else ""
        message = (
            _PATTERN_MESSAGE
            if detail["type"] == "string_pattern_mismatch"
            else detail["msg"].removeprefix("Value error, ")
        )
        messages.append(f"{DISPLAY_NAMES.get(field, field)}: {message}")
    return "; ".join(messages)
