from dataclasses import dataclass
from enum import StrEnum

import jwt

from app.core.config import Settings


class Role(StrEnum):
    VIEWER = "pricing.viewer"
    EDITOR = "pricing.editor"
    UPLOADER = "pricing.uploader"


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    roles: frozenset[str]

    def has_role(self, role: Role) -> bool:
        return role in self.roles


class AuthenticationError(Exception):
    pass


LOCAL_PRINCIPAL = Principal(subject="local.user", roles=frozenset(Role))


class Authenticator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._jwks = (
            jwt.PyJWKClient(settings.jwt_jwks_url, cache_keys=True)
            if settings.auth_mode == "jwt" and settings.jwt_jwks_url
            else None
        )

    def authenticate(self, token: str | None) -> Principal:
        if self._jwks is None:
            return LOCAL_PRINCIPAL
        if not token:
            raise AuthenticationError("Missing bearer token")

        try:
            signing_key = self._jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=self._settings.jwt_audience,
                issuer=self._settings.jwt_issuer,
                options={"require": ["exp", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid bearer token") from exc

        roles = claims.get(self._settings.jwt_roles_claim) or []
        if isinstance(roles, str):
            roles = [roles]
        subject = claims.get("preferred_username") or claims.get("email") or claims["sub"]
        return Principal(subject=str(subject), roles=frozenset(map(str, roles)))
