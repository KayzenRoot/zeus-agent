"""Verify the signed Zeus entitlement on this device, with offline grace."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

from hermes_constants import get_default_hermes_root
from utils import atomic_json_write, atomic_write_text

PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAfnOaaYWOq76IAhosov89hflCjYD340F1ydVLCtX5vQg=
-----END PUBLIC KEY-----
"""

DEFAULT_CLOUD_URL = "http://127.0.0.1:9121"
DEV_UNLOCK_ENV = "ZEUS_DEV_UNLOCK"


class EntitlementError(RuntimeError):
    """Activation or verification failed; the message is safe to show."""


class EntitlementRequired(EntitlementError):
    """The runtime has no valid entitlement for this device."""


@dataclass(frozen=True)
class EntitlementStatus:
    active: bool
    reason: str
    plan: str | None = None
    features: tuple[str, ...] = ()
    seats: int | None = None
    expires_at: int | None = None
    source: str = "token"

    def as_dict(self) -> dict[str, object]:
        return {
            "active": self.active,
            "reason": self.reason,
            "plan": self.plan,
            "features": list(self.features),
            "seats": self.seats,
            "expires_at": self.expires_at,
            "source": self.source,
        }


def entitlement_path() -> Path:
    return get_default_hermes_root() / "zeus-entitlement.json"


def device_id_path() -> Path:
    return get_default_hermes_root() / "zeus-device-id"


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def local_device_id() -> str:
    path = device_id_path()
    try:
        existing = path.read_text(encoding="utf-8").strip()
    except OSError:
        existing = ""
    if 8 <= len(existing) <= 128 and "\n" not in existing:
        return existing
    value = uuid.uuid4().hex
    atomic_write_text(path, value, mode=0o600, fsync_dir=True)
    return value


def verify_token(token: str, *, device_id: str) -> EntitlementStatus:
    import jwt

    if not token:
        return EntitlementStatus(False, "missing")
    try:
        claims = jwt.decode(
            token,
            PUBLIC_KEY_PEM,
            algorithms=["EdDSA"],
            issuer="zeus-cloud",
            options={"require": ["exp", "iat", "sub", "device_id"]},
        )
    except jwt.ExpiredSignatureError:
        return EntitlementStatus(False, "expired")
    except jwt.InvalidTokenError:
        return EntitlementStatus(False, "invalid")
    if str(claims.get("device_id") or "") != device_id:
        return EntitlementStatus(False, "device_mismatch")
    return EntitlementStatus(
        True,
        "active",
        plan=str(claims.get("plan") or "") or None,
        features=tuple(str(item) for item in claims.get("features") or ()),
        seats=int(claims["seats"]) if claims.get("seats") is not None else None,
        expires_at=int(claims["exp"]),
    )


def status() -> EntitlementStatus:
    if os.environ.get(DEV_UNLOCK_ENV) == "1":
        return EntitlementStatus(True, "dev_unlock", plan="dev", source="dev_unlock")
    data = _read_json(entitlement_path())
    if not data:
        return EntitlementStatus(False, "missing")
    token = str(data.get("token") or "")
    if not token:
        return EntitlementStatus(False, "invalid")
    return verify_token(token, device_id=local_device_id())


def require_entitlement() -> EntitlementStatus:
    current = status()
    if current.active:
        return current
    raise EntitlementRequired(
        "Zeus subscription required for this device "
        f"({current.reason}). Activate it in the Zeus app or run "
        "`hermes entitlement activate <code>`."
    )


def _cloud_url(value: str | None) -> str:
    candidate = (value or os.getenv("ZEUS_CLOUD_URL", DEFAULT_CLOUD_URL)).strip().rstrip("/")
    parsed = urllib.parse.urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise EntitlementError("ZEUS_CLOUD_URL must be an http(s) URL")
    return candidate


def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        raise EntitlementError(f"activation failed ({error.code}): {detail}") from error
    except urllib.error.URLError as error:
        raise EntitlementError(f"Zeus Cloud unreachable: {error.reason}") from error
    return body if isinstance(body, dict) else {}


def activate_with_code(
    code: str,
    *,
    cloud_url: str | None = None,
    device_id: str | None = None,
) -> EntitlementStatus:
    device = device_id or local_device_id()
    body = _post_json(
        f"{_cloud_url(cloud_url)}/api/device/exchange",
        {"code": code, "device_id": device},
    )
    token = str(body.get("token") or "")
    verdict = verify_token(token, device_id=device)
    if not verdict.active:
        raise EntitlementError(f"Zeus Cloud returned an unusable token ({verdict.reason})")
    atomic_json_write(
        entitlement_path(),
        {"token": token, "device_id": device, "saved_at": int(time.time())},
        mode=0o600,
        fsync_dir=True,
    )
    return verdict


def activation_url(*, site_url: str | None = None) -> str:
    base = (site_url or os.getenv("ZEUS_SITE_URL", "http://127.0.0.1:9120")).rstrip("/")
    return f"{base}/?device_id={urllib.parse.quote(local_device_id())}"
