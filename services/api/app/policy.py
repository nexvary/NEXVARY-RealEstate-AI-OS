from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import User, UserRole
from .security import decode_access_token


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class RequestContext:
    tenant_id: str
    user_id: str
    actor: str
    role: UserRole


def get_request_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Session = Depends(get_db),
) -> RequestContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    user = db.scalar(
        select(User).where(
            User.id == str(payload["sub"]),
            User.tenant_id == str(payload["tenant_id"]),
            User.is_active == 1,
        )
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or unavailable")

    return RequestContext(
        tenant_id=user.tenant_id,
        user_id=user.id,
        actor=user.email,
        role=user.role,
    )


def require_roles(*allowed: UserRole):
    def dependency(ctx: RequestContext = Depends(get_request_context)) -> RequestContext:
        if ctx.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this operation",
            )
        return ctx

    return dependency


write_sales = require_roles(
    UserRole.owner,
    UserRole.admin,
    UserRole.sales_manager,
    UserRole.sales_agent,
)
manage_inventory = require_roles(
    UserRole.owner,
    UserRole.admin,
    UserRole.sales_manager,
)
manage_users = require_roles(UserRole.owner, UserRole.admin)
