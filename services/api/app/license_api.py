from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .license_core import current_license_status, install_license


router = APIRouter(prefix="/api/v1/license", tags=["license"])


class LicenseActivation(BaseModel):
    license_document: dict[str, Any]
    agreement_accepted: bool


@router.get("/status")
def license_status() -> dict[str, Any]:
    return current_license_status()


@router.post("/activate")
def activate_license(payload: LicenseActivation) -> dict[str, Any]:
    if not payload.agreement_accepted:
        raise HTTPException(status_code=422, detail="The user agreement must be accepted")
    try:
        install_license(payload.license_document)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return current_license_status()
