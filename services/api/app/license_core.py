from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization


PRODUCT_ID = "real-estate-business-os"
PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEA2xSe4ZUhRpB7VXZgDRg7wgbTISdaxOPTzGQGR1gl3VU=
-----END PUBLIC KEY-----
"""


def _data_dir() -> Path:
    configured = os.getenv("NEXVARY_DATA_DIR") or os.getenv("REALESTATE_DATA_DIR")
    if configured:
        return Path(configured)
    return Path.cwd()


def license_path() -> Path:
    return _data_dir() / "license.json"


def _machine_seed() -> str:
    if platform.system() == "Windows":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            ) as key:
                return str(winreg.QueryValueEx(key, "MachineGuid")[0])
        except OSError:
            pass
    for candidate in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
        try:
            value = candidate.read_text(encoding="utf-8").strip()
            if value:
                return value
        except OSError:
            pass
    return f"{platform.node()}:{uuid.getnode()}"


def machine_code() -> str:
    digest = hashlib.sha256(f"{PRODUCT_ID}:{_machine_seed()}".encode("utf-8")).hexdigest().upper()
    return "-".join(digest[index:index + 4] for index in range(0, 24, 4))


def canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_license_document(
    document: dict[str, Any],
    *,
    expected_machine: str | None = None,
    public_key_pem: bytes = PUBLIC_KEY_PEM,
    now: datetime | None = None,
) -> dict[str, Any]:
    payload = document.get("payload")
    signature_text = document.get("signature")
    if not isinstance(payload, dict) or not isinstance(signature_text, str):
        raise ValueError("Invalid license document")
    try:
        signature = base64.b64decode(signature_text, validate=True)
        public_key = serialization.load_pem_public_key(public_key_pem)
        public_key.verify(signature, canonical_payload(payload))
    except (ValueError, TypeError, InvalidSignature) as exc:
        raise ValueError("License signature is invalid") from exc

    if payload.get("product") != PRODUCT_ID:
        raise ValueError("License is for a different product")
    actual_machine = (expected_machine or machine_code()).upper()
    licensed_machine = str(payload.get("machine_code") or "").upper()
    if licensed_machine not in {actual_machine, "*"}:
        raise ValueError("License belongs to another computer")

    expires_at = payload.get("expires_at")
    if expires_at:
        try:
            expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("License expiry date is invalid") from exc
        reference = now or datetime.now(timezone.utc)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry <= reference:
            raise ValueError("License has expired")
    return payload


def current_license_status() -> dict[str, Any]:
    path = license_path()
    base = {
        "machine_code": machine_code(),
        "valid": False,
        "state": "missing",
        "company": "",
        "customer": "",
        "edition": "",
        "expires_at": None,
        "features": [],
    }
    if not path.exists():
        return base
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        payload = verify_license_document(document)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        base["state"] = "invalid"
        base["message"] = str(exc)
        return base
    base.update(
        valid=True,
        state="active",
        company=str(payload.get("company") or ""),
        customer=str(payload.get("customer") or ""),
        edition=str(payload.get("edition") or "professional"),
        expires_at=payload.get("expires_at"),
        features=list(payload.get("features") or []),
        license_id=str(payload.get("license_id") or ""),
    )
    return base


def install_license(document: dict[str, Any]) -> dict[str, Any]:
    payload = verify_license_document(document)
    path = license_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return payload
