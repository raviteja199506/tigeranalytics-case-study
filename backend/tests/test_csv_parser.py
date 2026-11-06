import io
from datetime import date
from decimal import Decimal

import pytest

from app.services.csv_parser import CsvFormatError, PricingRow, RowError, parse_pricing_csv
from tests.conftest import HEADER


def parse(text: str) -> list[PricingRow | RowError]:
    return list(parse_pricing_csv(io.StringIO(text)))


def test_parses_valid_rows_with_display_headers() -> None:
    results = parse("Store ID,SKU,Product Name,Price,Date\nS001,SKU-1,Milk 1L,1.99,2026-01-15\n")

    assert results == [
        PricingRow(
            store_id="S001",
            sku="SKU-1",
            product_name="Milk 1L",
            price=Decimal("1.99"),
            price_date=date(2026, 1, 15),
        )
    ]


def test_accepts_snake_case_headers_in_any_order() -> None:
    results = parse("price,date,sku,store_id,product_name\n2.50,2026-02-01,A1,S9,Bread\n")

    assert isinstance(results[0], PricingRow)
    assert results[0].store_id == "S9"
    assert results[0].price == Decimal("2.50")


def test_handles_quoted_values_and_unicode() -> None:
    results = parse(f'{HEADER}\nS1,X1,"Café, crème 250g",3.4,2026-03-01\n')

    assert isinstance(results[0], PricingRow)
    assert results[0].product_name == "Café, crème 250g"


def test_missing_columns_raise_format_error() -> None:
    with pytest.raises(CsvFormatError, match="Missing required columns: Price, Date"):
        parse("Store ID,SKU,Product Name\nS1,X1,Thing\n")


def test_empty_file_raises_format_error() -> None:
    with pytest.raises(CsvFormatError, match="File is empty"):
        parse("")


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ("S1,X1,Thing,-1,2026-01-01", "Price: Input should be greater than 0"),
        ("S1,X1,Thing,abc,2026-01-01", "Price: Input should be a valid decimal"),
        ("S1,X1,Thing,1.123456,2026-01-01", "Price: Decimal input should have no more than 4"),
        ("S1,X1,Thing,1.00,15/01/2026", "Date: must be a date in YYYY-MM-DD format"),
        ("S1,,Thing,1.00,2026-01-01", "SKU: String should have at least 1 character"),
        ("S 1,X1,Thing,1.00,2026-01-01", "Store ID: may only contain letters, digits"),
        ("S1,X1,Thing,1.00", "Expected 5 columns but found 4"),
    ],
)
def test_invalid_rows_are_reported_with_reason(row: str, expected: str) -> None:
    results = parse(f"Store ID,SKU,Product Name,Price,Date\n{row}\n")

    assert len(results) == 1
    error = results[0]
    assert isinstance(error, RowError)
    assert error.row_number == 2
    assert expected in error.message


def test_blank_lines_are_skipped_and_row_numbers_track_source_lines() -> None:
    results = parse(
        "Store ID,SKU,Product Name,Price,Date\n"
        "S1,X1,Thing,1.00,2026-01-01\n"
        "\n"
        "S1,X2,Thing,bad,2026-01-01\n"
    )

    assert len(results) == 2
    assert isinstance(results[1], RowError)
    assert results[1].row_number == 4
