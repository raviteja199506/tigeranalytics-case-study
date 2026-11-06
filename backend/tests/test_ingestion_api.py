from fastapi.testclient import TestClient

from tests.conftest import HEADER, UploadCsv


def get_job(client: TestClient, job_id: str) -> dict:
    response = client.get(f"/api/v1/ingestions/{job_id}")
    assert response.status_code == 200
    return response.json()


def test_upload_is_accepted_and_processed(client: TestClient, upload_csv: UploadCsv) -> None:
    response = upload_csv(
        "S001,SKU-1,Milk 1L,1.99,2026-01-15",
        "S001,SKU-2,Bread,2.49,2026-01-15",
    )

    assert response.status_code == 202
    assert response.headers["Location"].endswith(f"/api/v1/ingestions/{response.json()['id']}")
    job = get_job(client, response.json()["id"])
    assert job["status"] == "completed"
    assert (job["total_rows"], job["accepted_rows"], job["rejected_rows"]) == (2, 2, 0)

    records = client.get("/api/v1/pricing-records", params={"store_id": "S001"}).json()
    assert records["total"] == 2
    assert {item["source_job_id"] for item in records["items"]} == {job["id"]}


def test_invalid_rows_are_rejected_and_reported(client: TestClient, upload_csv: UploadCsv) -> None:
    response = upload_csv(
        "S001,SKU-1,Milk 1L,1.99,2026-01-15",
        "S001,SKU-2,Bread,-5,2026-01-15",
        "S001,SKU-3,Eggs,3.10,not-a-date",
    )

    job = get_job(client, response.json()["id"])
    assert job["status"] == "completed_with_errors"
    assert (job["accepted_rows"], job["rejected_rows"]) == (1, 2)

    errors = client.get(f"/api/v1/ingestions/{job['id']}/errors").json()
    assert [error["row_number"] for error in errors] == [3, 4]
    assert "Price" in errors[0]["message"]


def test_missing_header_columns_fail_the_job(client: TestClient, upload_csv: UploadCsv) -> None:
    response = upload_csv("S001,SKU-1,1.99", header="Store ID,SKU,Price")

    job = get_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert "Missing required columns" in job["error_message"]


def test_file_with_only_invalid_rows_fails(client: TestClient, upload_csv: UploadCsv) -> None:
    response = upload_csv("S001,SKU-1,Milk,free,2026-01-15")

    job = get_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["rejected_rows"] == 1


def test_identical_file_is_rejected_as_duplicate(upload_csv: UploadCsv) -> None:
    row = "S001,SKU-1,Milk 1L,1.99,2026-01-15"
    assert upload_csv(row).status_code == 202

    duplicate = upload_csv(row, filename="again.csv")

    assert duplicate.status_code == 409
    assert "already uploaded" in duplicate.json()["detail"]


def test_reupload_upserts_on_store_sku_and_date(client: TestClient, upload_csv: UploadCsv) -> None:
    upload_csv("S001,SKU-1,Milk 1L,1.99,2026-01-15")
    upload_csv("S001,SKU-1,Milk 1L Organic,2.19,2026-01-15", "S001,SKU-1,Milk 1L,2.05,2026-01-16")

    records = client.get(
        "/api/v1/pricing-records", params={"sku": "SKU-1", "sort": "price_date"}
    ).json()

    assert records["total"] == 2
    first = records["items"][0]
    assert (first["product_name"], first["price"], first["version"]) == (
        "Milk 1L Organic",
        "2.1900",
        2,
    )


def test_duplicate_keys_within_file_keep_last_occurrence(
    client: TestClient, upload_csv: UploadCsv
) -> None:
    upload_csv("S001,SKU-1,Milk,1.00,2026-01-15", "S001,SKU-1,Milk,1.50,2026-01-15")

    items = client.get("/api/v1/pricing-records").json()["items"]

    assert [item["price"] for item in items] == ["1.5000"]


def test_large_file_is_processed_in_batches(client: TestClient, upload_csv: UploadCsv) -> None:
    rows = [
        f"S{store:03d},SKU-{sku},Item {sku},{sku}.99,2026-01-15"
        for store in range(5)
        for sku in range(1, 51)
    ]

    job = get_job(client, upload_csv(*rows).json()["id"])

    assert job["status"] == "completed"
    assert job["accepted_rows"] == 250
    assert client.get("/api/v1/pricing-records").json()["total"] == 250


def test_non_csv_upload_is_rejected(upload_csv: UploadCsv) -> None:
    response = upload_csv("S001,SKU-1,Milk,1.00,2026-01-15", filename="feed.xlsx")

    assert response.status_code == 422


def test_empty_upload_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/ingestions", files={"file": ("feed.csv", b"", "text/csv")})

    assert response.status_code == 422


def test_non_utf8_file_fails_gracefully(client: TestClient) -> None:
    content = f"{HEADER}\nS1,X1,Caf\xe9,1.00,2026-01-01\n".encode("latin-1")

    response = client.post("/api/v1/ingestions", files={"file": ("feed.csv", content, "text/csv")})

    job = get_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error_message"] == "File must be UTF-8 encoded"


def test_lists_recent_jobs_newest_first(client: TestClient, upload_csv: UploadCsv) -> None:
    upload_csv("S001,SKU-1,Milk,1.00,2026-01-15", filename="first.csv")
    upload_csv("S001,SKU-2,Milk,1.00,2026-01-15", filename="second.csv")

    jobs = client.get("/api/v1/ingestions").json()

    assert {job["filename"] for job in jobs} == {"first.csv", "second.csv"}


def test_unknown_job_returns_404(client: TestClient) -> None:
    assert client.get("/api/v1/ingestions/does-not-exist").status_code == 404
