"""Signed, device-bound entitlement tokens for the Zeus runtime."""

from __future__ import annotations

import base64
import time
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .settings import Settings

FEATURES: dict[str, list[str]] = {
    "monthly": ["constellation", "sync", "agents:5"],
    "quarterly": ["constellation", "sync", "agents:5", "priority_support"],
    "semiannual": ["constellation", "sync", "agents:8", "priority_support"],
    "annual": ["constellation", "sync", "agents:10", "priority_support"],
}

SEATS: dict[str, int] = {
    "monthly": 5,
    "quarterly": 5,
    "semiannual": 8,
    "annual": 10,
}


class EntitlementNotConfigured(RuntimeError):
    """The deployment has no signing key; the endpoint must fail closed."""


def plan_features(plan: str | None) -> list[str]:
    return list(FEATURES.get(plan or "", []))


def plan_seats(plan: str | None) -> int:
    return SEATS.get(plan or "", 1)


def is_active(row: dict[str, Any] | None, *, now: int | None = None) -> bool:
    if not row or row.get("status") not in {"active", "trialing"}:
        return False
    period_end = row.get("current_period_end")
    if period_end is None:
        return True
    return int(period_end) > (int(time.time()) if now is None else now)


def _signing_key(settings: Settings) -> Ed25519PrivateKey:
    encoded = settings.entitlement_private_key_b64
    if not encoded:
        raise EntitlementNotConfigured("ZEUS_ENTITLEMENT_PRIVATE_KEY_B64 is not configured")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except ValueError as error:
        raise EntitlementNotConfigured("entitlement signing key is not valid base64") from error
    if len(raw) != 32:
        raise EntitlementNotConfigured("entitlement signing key must be 32 raw bytes")
    return Ed25519PrivateKey.from_private_bytes(raw)


def sign_entitlement(
    settings: Settings,
    row: dict[str, Any],
    *,
    device_id: str,
    now: int | None = None,
) -> dict[str, Any]:
    if settings.entitlement_ttl_days <= 0:
        raise EntitlementNotConfigured("entitlement TTL must be positive")
    issued_at = int(time.time()) if now is None else now
    expires_at = issued_at + settings.entitlement_ttl_days * 86_400
    plan = str(row["plan"])
    payload = {
        "iss": "zeus-cloud",
        "sub": str(row["user_id"]),
        "plan": plan,
        "features": plan_features(plan),
        "seats": plan_seats(plan),
        "device_id": device_id,
        "iat": issued_at,
        "exp": expires_at,
    }
    token = jwt.encode(payload, _signing_key(settings), algorithm="EdDSA")
    return {
        "token": token,
        "expires_at": expires_at,
        "plan": plan,
        "features": payload["features"],
        "seats": payload["seats"],
    }
