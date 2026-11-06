from collections.abc import Callable, Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import AuthenticationError, Authenticator, Principal, Role
from app.db.database import Database
from app.infrastructure.storage import FileStorage
from app.services.ingestion import IngestionService
from app.services.pricing import PricingService

_bearer = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_storage(request: Request) -> FileStorage:
    return request.app.state.storage


def get_session(database: Annotated[Database, Depends(get_database)]) -> Iterator[Session]:
    with database.session() as session:
        yield session


def get_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    authenticator: Authenticator = request.app.state.authenticator
    try:
        return authenticator.authenticate(credentials.credentials if credentials else None)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_role(role: Role) -> Callable[[Principal], Principal]:
    def dependency(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
        if not principal.has_role(role):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Requires role '{role}'")
        return principal

    return dependency


SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[Database, Depends(get_database)]
StorageDep = Annotated[FileStorage, Depends(get_storage)]
SessionDep = Annotated[Session, Depends(get_session)]

ViewerDep = Annotated[Principal, Depends(require_role(Role.VIEWER))]
EditorDep = Annotated[Principal, Depends(require_role(Role.EDITOR))]
UploaderDep = Annotated[Principal, Depends(require_role(Role.UPLOADER))]


def get_pricing_service(session: SessionDep) -> PricingService:
    return PricingService(session)


def get_ingestion_service(
    session: SessionDep, storage: StorageDep, settings: SettingsDep
) -> IngestionService:
    return IngestionService(session, storage, settings)


PricingServiceDep = Annotated[PricingService, Depends(get_pricing_service)]
IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]
