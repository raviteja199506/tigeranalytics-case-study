from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.models import Base

HEADER = "Store ID,SKU,Product Name,Price,Date"

UploadCsv = Callable[..., httpx.Response]


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        log_level="WARNING",
        database_url=f"sqlite:///{tmp_path / 'pricing.db'}",
        storage_dir=tmp_path / "uploads",
        ingestion_batch_size=100,
        max_reported_errors=50,
        auth_mode="disabled",
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    application = create_app(settings)
    Base.metadata.create_all(application.state.database.engine)
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def upload_csv(client: TestClient) -> UploadCsv:
    def upload(*rows: str, header: str = HEADER, filename: str = "feed.csv") -> httpx.Response:
        content = "\n".join([header, *rows]) + "\n"
        return client.post(
            "/api/v1/ingestions",
            files={"file": (filename, content.encode("utf-8"), "text/csv")},
        )

    return upload
