from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from .models import UserRole


@dataclass(frozen=True)
class RequestContext:
    tenant_id: str
    actor: str
    role: UserRole


def get_request_context(
    x_tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    x_actor: Annotated[str, Header(alias="X-Actor")] = "api",
    x_role: Annotated[UserRole, Header(alias="X-Role")] = UserRole.viewer,
) -> RequestContext:
    return RequestContext(tenant_id=x_tenant_id, actor=x_actor, role=x_role)


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
