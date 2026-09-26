from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .saas_models import PlatformAdmin
from .security import decode_platform_token


platform_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class PlatformContext:
    admin_id: str
    email: str
    display_name: str


def get_platform_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(platform_bearer)],
    db: Session = Depends(get_db),
) -> PlatformContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Platform administrator token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_platform_token(credentials.credentials)
    admin = db.scalar(
        select(PlatformAdmin).where(
            PlatformAdmin.id == str(payload["sub"]),
            PlatformAdmin.is_active == 1,
        )
    )
    if admin is None:
        raise HTTPException(status_code=401, detail="Platform administrator is inactive or unavailable")

    return PlatformContext(admin_id=admin.id, email=admin.email, display_name=admin.display_name)
