from __future__ import annotations

import os
import secrets
from typing import Annotated

from fastapi import Header, HTTPException, Request, Response

OPERATOR_KEY_ENV = "SEO_OPERATOR_KEY"
OPERATOR_HEADER = "X-SEO-Operator-Key"


def require_operator_key(
    x_seo_operator_key: Annotated[str | None, Header(alias=OPERATOR_HEADER)] = None,
) -> None:
    expected = os.getenv(OPERATOR_KEY_ENV, "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Sensitive operations are disabled until SEO_OPERATOR_KEY is configured.",
        )
    supplied = (x_seo_operator_key or "").strip()
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Valid SEO operator key required.")


def apply_security_headers(request: Request, response: Response) -> Response:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; "
        "frame-ancestors 'none'; form-action 'self'",
    )
    if request.url.scheme == "https":
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    return response
