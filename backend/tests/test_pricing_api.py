import pytest
from fastapi.testclient import TestClient

from tests.conftest import UploadCsv

SEARCH_URL = "/api/v1/pricing-records"


@pytest.fixture
def seeded(upload_csv: UploadCsv) -> None:
    response = upload_csv(
        "S001,SKU-1,Whole Milk 1L,1.99,2026-01-10",
        "S001,SKU-2,Sourdough Bread,4.50,2026-01-11",
        "S002,SKU-1,Whole Milk 1L,2.09,2026-01-10",
        "S002,SKU-3,Free Range Eggs 12pk,5.75,2026-01-12",
        "S003,SKU-4,100% Orange Juice,3.25,2026-01-13",
    )
    assert response.status_code == 202


def search(client: TestClient, **params: object) -> dict:
    response = client.get(SEARCH_URL, params=params)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.usefixtures("seeded")
class TestSearch:
    def test_filters_by_store(self, client: TestClient) -> None:
        result = search(client, store_id="S001")
        assert {item["sku"] for item in result["items"]} == {"SKU-1", "SKU-2"}

    def test_filters_by_sku_across_stores(self, client: TestClient) -> None:
        result = search(client, sku="SKU-1")
        assert {item["store_id"] for item in result["items"]} == {"S001", "S002"}

    def test_product_name_is_case_insensitive_contains(self, client: TestClient) -> None:
        result = search(client, product_name="milk")
        assert result["total"] == 2

    def test_product_name_wildcards_are_escaped(self, client: TestClient) -> None:
        result = search(client, product_name="100%")
        assert [item["sku"] for item in result["items"]] == ["SKU-4"]

    def test_filters_by_price_range(self, client: TestClient) -> None:
        result = search(client, min_price="2", max_price="5", sort="price")
        assert [item["price"] for item in result["items"]] == ["2.0900", "3.2500", "4.5000"]

    def test_filters_by_date_range(self, client: TestClient) -> None:
        result = search(client, date_from="2026-01-11", date_to="2026-01-12")
        assert {item["sku"] for item in result["items"]} == {"SKU-2", "SKU-3"}

    def test_combines_criteria(self, client: TestClient) -> None:
        result = search(client, store_id="S002", product_name="eggs", max_price="10")
        assert [item["sku"] for item in result["items"]] == ["SKU-3"]

    def test_paginates_results(self, client: TestClient) -> None:
        first = search(client, page=1, page_size=2, sort="price")
        third = search(client, page=3, page_size=2, sort="price")

        assert first["total"] == 5
        assert [item["price"] for item in first["items"]] == ["1.9900", "2.0900"]
        assert [item["price"] for item in third["items"]] == ["5.7500"]

    def test_sorts_descending(self, client: TestClient) -> None:
        result = search(client, sort="-price")
        assert result["items"][0]["price"] == "5.7500"

    @pytest.mark.parametrize(
        "params",
        [
            {"min_price": "10", "max_price": "1"},
            {"date_from": "2026-02-01", "date_to": "2026-01-01"},
            {"sort": "drop_table"},
            {"page_size": 1000},
            {"unknown": "x"},
        ],
    )
    def test_rejects_invalid_criteria(self, client: TestClient, params: dict) -> None:
        assert client.get(SEARCH_URL, params=params).status_code == 422


@pytest.mark.usefixtures("seeded")
class TestUpdate:
    @staticmethod
    def record(client: TestClient, sku: str = "SKU-2") -> dict:
        return search(client, store_id="S001", sku=sku)["items"][0]

    def test_updates_price_and_name_and_records_audit(self, client: TestClient) -> None:
        record = self.record(client)

        response = client.patch(
            f"{SEARCH_URL}/{record['id']}",
            json={"price": "4.25", "product_name": "Sourdough Loaf", "version": record["version"]},
        )

        assert response.status_code == 200
        updated = response.json()
        assert (updated["price"], updated["product_name"]) == ("4.2500", "Sourdough Loaf")
        assert updated["version"] == record["version"] + 1
        assert updated["updated_by"] == "local.user"

        history = client.get(f"{SEARCH_URL}/{record['id']}/history").json()
        assert len(history) == 1
        assert history[0]["changes"]["price"] == {"old": "4.5000", "new": "4.25"}
        assert history[0]["version"] == updated["version"]

    def test_stale_version_is_rejected(self, client: TestClient) -> None:
        record = self.record(client)
        url = f"{SEARCH_URL}/{record['id']}"
        assert client.patch(url, json={"price": "4.00", "version": 1}).status_code == 200

        conflict = client.patch(url, json={"price": "3.00", "version": 1})

        assert conflict.status_code == 409
        assert client.get(url).json()["price"] == "4.0000"

    def test_unchanged_values_do_not_bump_version(self, client: TestClient) -> None:
        record = self.record(client)

        response = client.patch(
            f"{SEARCH_URL}/{record['id']}", json={"price": "4.5", "version": record["version"]}
        )

        assert response.json()["version"] == record["version"]
        assert client.get(f"{SEARCH_URL}/{record['id']}/history").json() == []

    @pytest.mark.parametrize(
        "payload",
        [
            {"version": 1},
            {"price": "-1", "version": 1},
            {"price": "1.123456", "version": 1},
            {"product_name": "", "version": 1},
            {"store_id": "S999", "price": "1", "version": 1},
        ],
    )
    def test_rejects_invalid_payloads(self, client: TestClient, payload: dict) -> None:
        record = self.record(client)
        assert client.patch(f"{SEARCH_URL}/{record['id']}", json=payload).status_code == 422

    def test_missing_record_returns_404(self, client: TestClient) -> None:
        response = client.patch(f"{SEARCH_URL}/999999", json={"price": "1", "version": 1})
        assert response.status_code == 404
        assert client.get(f"{SEARCH_URL}/999999/history").status_code == 404
