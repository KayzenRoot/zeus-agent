"""Behaviour contracts for the local Zeus entitlement verifier and turn gate."""

from __future__ import annotations

import json
import time
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import zeus_entitlement
from agent.turn_facade import TurnFacadeMixin


def _keys() -> tuple[Ed25519PrivateKey, str]:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private, public


def _token(
    private: Ed25519PrivateKey,
    *,
    device_id: str = "device-abcdefgh",
    exp: int | None = None,
    issuer: str = "zeus-cloud",
) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": issuer,
            "sub": "user_123",
            "plan": "annual",
            "features": ["agents:10"],
            "seats": 10,
            "device_id": device_id,
            "iat": now,
            "exp": exp if exp is not None else now + 3600,
        },
        private,
        algorithm="EdDSA",
    )


@pytest.fixture
def paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    token_path = tmp_path / "zeus-entitlement.json"
    device_path = tmp_path / "zeus-device-id"
    monkeypatch.setattr(zeus_entitlement, "entitlement_path", lambda: token_path)
    monkeypatch.setattr(zeus_entitlement, "device_id_path", lambda: device_path)
    return token_path, device_path


def test_valid_token_is_device_bound(paths, monkeypatch: pytest.MonkeyPatch) -> None:
    private, public = _keys()
    monkeypatch.setattr(zeus_entitlement, "PUBLIC_KEY_PEM", public)
    token = _token(private)

    active = zeus_entitlement.verify_token(token, device_id="device-abcdefgh")
    assert active.active is True
    assert active.plan == "annual"
    assert active.seats == 10
    assert active.features == ("agents:10",)

    wrong = zeus_entitlement.verify_token(token, device_id="device-other-12")
    assert wrong.active is False
    assert wrong.reason == "device_mismatch"


def test_expired_and_invalid_tokens_fail_closed(paths, monkeypatch: pytest.MonkeyPatch) -> None:
    private, public = _keys()
    monkeypatch.setattr(zeus_entitlement, "PUBLIC_KEY_PEM", public)

    expired = zeus_entitlement.verify_token(
        _token(private, exp=int(time.time()) - 10),
        device_id="device-abcdefgh",
    )
    assert expired.active is False
    assert expired.reason == "expired"

    wrong_issuer = zeus_entitlement.verify_token(
        _token(private, issuer="someone-else"),
        device_id="device-abcdefgh",
    )
    assert wrong_issuer.active is False
    assert wrong_issuer.reason == "invalid"


def test_dev_unlock_is_explicit_and_runtime_checked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZEUS_DEV_UNLOCK", "1")
    assert zeus_entitlement.status().reason == "dev_unlock"

    monkeypatch.setenv("ZEUS_DEV_UNLOCK", "true")
    assert zeus_entitlement.status().active is False


def test_status_reads_the_local_token(paths, monkeypatch: pytest.MonkeyPatch) -> None:
    token_path, device_path = paths
    private, public = _keys()
    monkeypatch.setattr(zeus_entitlement, "PUBLIC_KEY_PEM", public)
    monkeypatch.delenv("ZEUS_DEV_UNLOCK", raising=False)
    device_path.write_text("device-abcdefgh", encoding="utf-8")
    token_path.write_text(
        json.dumps({"token": _token(private), "device_id": "device-abcdefgh"}),
        encoding="utf-8",
    )

    current = zeus_entitlement.status()
    assert current.active is True
    assert current.plan == "annual"


def test_activate_with_code_persists_the_token(
    paths, monkeypatch: pytest.MonkeyPatch
) -> None:
    token_path, device_path = paths
    private, public = _keys()
    monkeypatch.setattr(zeus_entitlement, "PUBLIC_KEY_PEM", public)
    device_path.write_text("device-abcdefgh", encoding="utf-8")
    monkeypatch.setattr(
        zeus_entitlement,
        "_post_json",
        lambda _url, _payload: {"token": _token(private, device_id="device-abcdefgh")},
    )

    result = zeus_entitlement.activate_with_code(
        "code-abcdefghijklmnop",
        cloud_url="http://127.0.0.1:9121",
    )

    assert result.active is True
    saved = json.loads(token_path.read_text(encoding="utf-8"))
    assert saved["device_id"] == "device-abcdefgh"
    assert device_path.read_text(encoding="utf-8") == "device-abcdefgh"


def test_require_entitlement_refuses_without_a_token(
    paths, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ZEUS_DEV_UNLOCK", raising=False)

    with pytest.raises(zeus_entitlement.EntitlementRequired, match="subscription required"):
        zeus_entitlement.require_entitlement()


def test_turn_gate_returns_a_typed_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse() -> None:
        raise zeus_entitlement.EntitlementRequired("Zeus subscription required")

    monkeypatch.setattr(zeus_entitlement, "require_entitlement", refuse)

    class Dummy(TurnFacadeMixin):
        pass

    result = Dummy().run_conversation("hello")

    assert result["completed"] is False
    assert result["failed"] is True
    assert result["api_calls"] == 0
    assert result["failure_reason"] == "entitlement_required"
    assert "subscription required" in result["final_response"]
