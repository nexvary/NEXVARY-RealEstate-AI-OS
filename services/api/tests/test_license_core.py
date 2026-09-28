from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.license_core import PRODUCT_ID, canonical_payload, verify_license_document


def signed_document(machine: str, expires_at: str | None = None):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    payload = {
        "product": PRODUCT_ID,
        "license_id": "TEST-001",
        "customer": "Test Customer",
        "company": "Test Realty",
        "machine_code": machine,
        "edition": "professional",
        "features": ["crm", "inventory"],
        "issued_at": "2026-09-27T00:00:00Z",
        "expires_at": expires_at,
    }
    signature = private_key.sign(canonical_payload(payload))
    return {"payload": payload, "signature": base64.b64encode(signature).decode("ascii")}, public_key


def test_signed_license_is_bound_to_machine():
    document, public_key = signed_document("AAAA-BBBB-CCCC-DDDD-EEEE-FFFF")
    verified = verify_license_document(
        document,
        expected_machine="AAAA-BBBB-CCCC-DDDD-EEEE-FFFF",
        public_key_pem=public_key,
    )
    assert verified["company"] == "Test Realty"

    with pytest.raises(ValueError, match="another computer"):
        verify_license_document(document, expected_machine="OTHER-MACHINE", public_key_pem=public_key)


def test_tampering_and_expiry_are_rejected():
    expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    document, public_key = signed_document("MACHINE", expires_at=expired)
    with pytest.raises(ValueError, match="expired"):
        verify_license_document(document, expected_machine="MACHINE", public_key_pem=public_key)

    document, public_key = signed_document("MACHINE")
    document["payload"]["edition"] = "enterprise"
    with pytest.raises(ValueError, match="signature"):
        verify_license_document(document, expected_machine="MACHINE", public_key_pem=public_key)
