from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Query, Request, Response, UploadFile, status

from app.api.deps import (
    DatabaseDep,
    IngestionServiceDep,
    SettingsDep,
    StorageDep,
    UploaderDep,
    ViewerDep,
)
from app.schemas.ingestion import IngestionErrorRead, IngestionJobRead
from app.services.ingestion import run_ingestion

router = APIRouter(prefix="/ingestions", tags=["ingestions"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=IngestionJobRead)
def upload_pricing_feed(
    file: Annotated[UploadFile, File(description="CSV pricing feed")],
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    service: IngestionServiceDep,
    database: DatabaseDep,
    storage: StorageDep,
    settings: SettingsDep,
    principal: UploaderDep,
) -> IngestionJobRead:
    job = service.submit(file.file, file.filename or "upload.csv", principal.subject)
    background_tasks.add_task(run_ingestion, job.id, database, storage, settings)
    response.headers["Location"] = str(request.url_for("get_ingestion_job", job_id=job.id))
    return IngestionJobRead.model_validate(job)


@router.get("", response_model=list[IngestionJobRead])
def list_ingestion_jobs(
    service: IngestionServiceDep,
    _: ViewerDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[IngestionJobRead]:
    return [IngestionJobRead.model_validate(job) for job in service.list_recent(limit)]


@router.get("/{job_id}", response_model=IngestionJobRead)
def get_ingestion_job(job_id: str, service: IngestionServiceDep, _: ViewerDep) -> IngestionJobRead:
    return IngestionJobRead.model_validate(service.get(job_id))


@router.get("/{job_id}/errors", response_model=list[IngestionErrorRead])
def list_ingestion_errors(
    job_id: str,
    service: IngestionServiceDep,
    _: ViewerDep,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> list[IngestionErrorRead]:
    return [IngestionErrorRead.model_validate(e) for e in service.list_errors(job_id, limit)]
