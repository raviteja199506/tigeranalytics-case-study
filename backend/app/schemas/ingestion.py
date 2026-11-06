from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import IngestionStatus


class IngestionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    status: IngestionStatus
    size_bytes: int
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    error_message: str | None
    uploaded_by: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class IngestionErrorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    row_number: int
    message: str
    raw_line: str | None
