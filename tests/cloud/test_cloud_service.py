"""Behaviour contracts for the Zeus Cloud checkout and entitlement API."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from fastapi.testclient import TestClient

from cloud.service import stripe_api
from cloud.service.app import create_app
from cloud.service.settings import Settings

WEBHOOK_SECRET = "whsec_test_secret"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    plans_path = tmp_path / "plans.json"
    plans_path.write_text(
        json.dumps(
            {
                "currency": "brl",
                "trial_days": 2,
                "plans": {
                    "monthly": {
                        "name": "Zeus Pro - Mensal",
                        "amount": 99000,
                        "interval": "month",
                        "price_id": "price_monthly",
                        "payment_link": "https://buy.stripe.com/test_monthly",
                    },
                    "annual": {
                        "name": "Zeus Pro - Anual",
                        "amount": 948000,
                        "interval": "year",
                        "price_id": "price_annual",
                        "payment_link": "https://buy.stripe.com/test_annual",
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return Settings(
        stripe_secret="sk_test_fake",
        stripe_webhook_secret=WEBHOOK_SECRET,
        clerk_frontend_api="",
        db_path=tmp_path / "entitlements.db",
        plans_path=plans_path,
        success_url="http://127.0.0.1:9120/?checkout=success",
        cancel_url="http://127.0.0.1:9120/?checkout=cancel",
        trial_days=2,
        entitlement_private_key_b64=base64.b64encode(
            Ed25519PrivateKey.generate().private_bytes(
                serialization.Encoding.Raw,
                serialization.PrivateFormat.Raw,
                serialization.NoEncryption(),
            )
        ).decode(),
    )


@pytest.fixture
def client(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ZEUS_CLOUD_DEV_AUTH", "1")
    return TestClient(create_app(settings))


def _headers(user: str = "user_123") -> dict[str, str]:
    return {"Authorization": f"Bearer dev:{user}"}


def _sign(payload: bytes, *, timestamp: int | None = None) -> str:
    timestamp = int(time.time()) if timestamp is None else timestamp
    signed = f"{timestamp}.".encode() + payload
    digest = hmac.new(WEBHOOK_SECRET.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def _post_event(client: TestClient, event: dict[str, Any]) -> Any:
    payload = json.dumps(event).encode()
    return client.post(
        "/api/stripe/webhook",
        content=payload,
        headers={"stripe-signature": _sign(payload)},
    )


def test_health_and_plans_are_public(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"ok": True, "service": "zeus-cloud", "mode": "test"}

    plans = client.get("/api/plans")
    assert plans.status_code == 200
    assert plans.json()["plans"]["monthly"]["price_id"] == "price_monthly"


def test_entitlement_requires_a_bearer_token(client: TestClient) -> None:
    assert client.get("/api/entitlement").status_code == 401


def test_live_stripe_key_is_refused_until_the_owner_opts_in(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ZEUS_CLOUD_ALLOW_LIVE", raising=False)
    live = replace(settings, stripe_secret="sk_live_fake")

    with pytest.raises(RuntimeError, match="refusing live Stripe key"):
        create_app(live)

    monkeypatch.setenv("ZEUS_CLOUD_ALLOW_LIVE", "1")
    monkeypatch.setenv("ZEUS_CLOUD_DEV_AUTH", "1")
    client = TestClient(create_app(live))
    assert client.get("/api/entitlement", headers=_headers()).status_code == 403


def test_unknown_user_has_no_entitlement(client: TestClient) -> None:
    response = client.get("/api/entitlement", headers=_headers())
    assert response.status_code == 200
    assert response.json() == {
        "active": False,
        "plan": None,
        "status": "inactive",
        "current_period_end": None,
        "features": [],
    }


def _public_key(settings: Settings) -> bytes:
    raw = base64.b64decode(settings.entitlement_private_key_b64)
    private = Ed25519PrivateKey.from_private_bytes(raw)
    return private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def _seed_active(
    client: TestClient,
    user_id: str,
    plan: str = "annual",
    customer_id: str | None = None,
) -> None:
    client.app.state.store.upsert(
        user_id=user_id,
        plan=plan,
        status="active",
        current_period_end=int(time.time()) + 86_400,
        customer_id=customer_id,
    )


def test_entitlement_token_is_device_bound_and_signed(
    client: TestClient, settings: Settings
) -> None:
    _seed_active(client, "user_signed")

    response = client.post(
        "/api/entitlement/token",
        json={"device_id": "device-abcdefgh"},
        headers=_headers("user_signed"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "annual"
    assert body["seats"] == 10
    assert "agents:10" in body["features"]
    claims = jwt.decode(body["token"], _public_key(settings), algorithms=["EdDSA"])
    assert claims["iss"] == "zeus-cloud"
    assert claims["sub"] == "user_signed"
    assert claims["plan"] == "annual"
    assert claims["device_id"] == "device-abcdefgh"
    assert claims["seats"] == 10
    assert claims["exp"] - claims["iat"] == 7 * 86_400


def test_entitlement_token_rejects_an_inactive_subscription(client: TestClient) -> None:
    response = client.post(
        "/api/entitlement/token",
        json={"device_id": "device-abcdefgh"},
        headers=_headers("user_inactive"),
    )
    assert response.status_code == 403


def test_entitlement_token_requires_a_device_id(client: TestClient) -> None:
    _seed_active(client, "user_no_device")

    response = client.post(
        "/api/entitlement/token",
        json={"device_id": "short"},
        headers=_headers("user_no_device"),
    )
    assert response.status_code == 422


def test_entitlement_token_fails_closed_without_a_signing_key(
    client: TestClient, settings: Settings
) -> None:
    _seed_active(client, "user_no_key")
    app = create_app(replace(settings, entitlement_private_key_b64=""))
    unsigned = TestClient(app)

    response = unsigned.post(
        "/api/entitlement/token",
        json={"device_id": "device-abcdefgh"},
        headers=_headers("user_no_key"),
    )
    assert response.status_code == 503


def test_device_code_exchange_returns_a_signed_token(
    client: TestClient, settings: Settings
) -> None:
    _seed_active(client, "user_device")
    authorized = client.post(
        "/api/device/authorize",
        json={"device_id": "device-abcdefgh"},
        headers=_headers("user_device"),
    )
    assert authorized.status_code == 200
    code = authorized.json()["code"]

    exchanged = client.post(
        "/api/device/exchange",
        json={"code": code, "device_id": "device-abcdefgh"},
    )
    assert exchanged.status_code == 200
    body = exchanged.json()
    assert body["plan"] == "annual"
    claims = jwt.decode(body["token"], _public_key(settings), algorithms=["EdDSA"])
    assert claims["device_id"] == "device-abcdefgh"
    assert claims["sub"] == "user_device"

    reused = client.post(
        "/api/device/exchange",
        json={"code": code, "device_id": "device-abcdefgh"},
    )
    assert reused.status_code == 400


def test_device_code_is_bound_to_the_requesting_device(client: TestClient) -> None:
    _seed_active(client, "user_device_bind")
    code = client.post(
        "/api/device/authorize",
        json={"device_id": "device-abcdefgh"},
        headers=_headers("user_device_bind"),
    ).json()["code"]

    wrong = client.post(
        "/api/device/exchange",
        json={"code": code, "device_id": "device-other-123"},
    )
    assert wrong.status_code == 400

    correct = client.post(
        "/api/device/exchange",
        json={"code": code, "device_id": "device-abcdefgh"},
    )
    assert correct.status_code == 200


def test_device_authorization_requires_an_active_subscription(client: TestClient) -> None:
    response = client.post(
        "/api/device/authorize",
        json={"device_id": "device-abcdefgh"},
        headers=_headers("user_no_sub"),
    )
    assert response.status_code == 403


def test_expired_device_code_is_rejected(client: TestClient) -> None:
    _seed_active(client, "user_expired_code")
    code = "expired-code-abcdefgh"
    client.app.state.store.create_device_code(
        code_hash=hashlib.sha256(code.encode()).hexdigest(),
        user_id="user_expired_code",
        device_id="device-abcdefgh",
        expires_at=int(time.time()) - 1,
    )

    response = client.post(
        "/api/device/exchange",
        json={"code": code, "device_id": "device-abcdefgh"},
    )
    assert response.status_code == 400


def test_device_exchange_rechecks_the_subscription(client: TestClient) -> None:
    _seed_active(client, "user_canceled_device")
    code = client.post(
        "/api/device/authorize",
        json={"device_id": "device-abcdefgh"},
        headers=_headers("user_canceled_device"),
    ).json()["code"]
    client.app.state.store.upsert(
        user_id="user_canceled_device",
        plan="annual",
        status="canceled",
        current_period_end=int(time.time()) + 86_400,
    )

    response = client.post(
        "/api/device/exchange",
        json={"code": code, "device_id": "device-abcdefgh"},
    )
    assert response.status_code == 403


def test_tracked_public_key_is_a_valid_ed25519_key() -> None:
    root = Path(__file__).resolve().parents[2]
    pem = (root / "cloud" / "entitlement_public_key.pem").read_bytes()
    assert isinstance(serialization.load_pem_public_key(pem), Ed25519PublicKey)


def test_billing_portal_returns_the_stripe_url_for_a_customer(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_active(client, "user_portal", customer_id="cus_portal")
    calls: dict[str, str] = {}

    def fake_portal(_settings: Settings, *, customer_id: str, return_url: str) -> dict[str, str]:
        calls.update(customer_id=customer_id, return_url=return_url)
        return {"url": "https://billing.stripe.test/session"}

    monkeypatch.setattr("cloud.service.app.stripe_api.create_billing_portal_session", fake_portal)

    response = client.post("/api/billing/portal", headers=_headers("user_portal"))

    assert response.status_code == 200
    assert response.json() == {"url": "https://billing.stripe.test/session"}
    assert calls == {
        "customer_id": "cus_portal",
        "return_url": "http://127.0.0.1:9120/?portal=done",
    }


def test_billing_portal_rejects_an_account_without_a_stripe_customer(
    client: TestClient,
) -> None:
    _seed_active(client, "user_no_customer")

    response = client.post("/api/billing/portal", headers=_headers("user_no_customer"))
    assert response.status_code == 404


def test_billing_portal_rejects_an_inactive_subscription(client: TestClient) -> None:
    response = client.post("/api/billing/portal", headers=_headers("user_inactive_portal"))
    assert response.status_code == 403


def test_billing_portal_session_posts_customer_and_return_url(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        _secret: str,
        method: str,
        path: str,
        data: dict[str, str] | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, str]:
        captured.update(method=method, path=path, data=data or {}, key=idempotency_key)
        return {"url": "https://billing.stripe.test/session"}

    monkeypatch.setattr(stripe_api, "_request", fake_request)

    result = stripe_api.create_billing_portal_session(
        settings,
        customer_id="cus_1",
        return_url="http://127.0.0.1:9120/?portal=done",
    )

    assert result == {"url": "https://billing.stripe.test/session"}
    assert captured["path"] == "/billing_portal/sessions"
    assert captured["data"] == {
        "customer": "cus_1",
        "return_url": "http://127.0.0.1:9120/?portal=done",
    }


def test_checkout_forwards_the_authenticated_user_and_plan(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, str] = {}

    def fake_checkout(_settings: Settings, *, user_id: str, plan_key: str) -> dict[str, str]:
        calls.update(user_id=user_id, plan_key=plan_key)
        return {"id": "cs_test_1", "url": "https://checkout.stripe.test/cs_test_1"}

    monkeypatch.setattr("cloud.service.app.stripe_api.create_checkout_session", fake_checkout)

    response = client.post("/api/checkout", json={"plan": "monthly"}, headers=_headers())

    assert response.status_code == 200
    assert response.json() == {
        "url": "https://checkout.stripe.test/cs_test_1",
        "id": "cs_test_1",
    }
    assert calls == {"user_id": "user_123", "plan_key": "monthly"}


def test_checkout_rejects_an_unknown_plan(client: TestClient) -> None:
    response = client.post("/api/checkout", json={"plan": "lifetime"}, headers=_headers())
    assert response.status_code == 400
    assert "unknown plan" in response.json()["detail"]


def test_checkout_carries_identity_onto_the_subscription(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        _secret: str,
        method: str,
        path: str,
        data: dict[str, str] | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, str]:
        captured.update(method=method, path=path, data=data or {}, key=idempotency_key)
        return {"id": "cs_test_1", "url": "https://checkout.stripe.test/cs_test_1"}

    monkeypatch.setattr(stripe_api, "_request", fake_request)

    stripe_api.create_checkout_session(settings, user_id="user_42", plan_key="monthly")

    data = captured["data"]
    assert captured["path"] == "/checkout/sessions"
    assert data["subscription_data[metadata][zeus_user_id]"] == "user_42"
    assert data["subscription_data[metadata][zeus_plan]"] == "monthly"
    assert data["subscription_data[trial_period_days]"] == "2"
    assert data["line_items[0][price]"] == "price_monthly"
    assert captured["key"] == "zeus-checkout-user_42-monthly"


def test_webhook_rejects_missing_and_invalid_signatures(client: TestClient) -> None:
    payload = json.dumps({"type": "checkout.session.completed"}).encode()

    missing = client.post("/api/stripe/webhook", content=payload)
    assert missing.status_code == 400

    invalid = client.post(
        "/api/stripe/webhook",
        content=payload,
        headers={"stripe-signature": "t=1,v1=deadbeef"},
    )
    assert invalid.status_code == 400

    stale = client.post(
        "/api/stripe/webhook",
        content=payload,
        headers={"stripe-signature": _sign(payload, timestamp=int(time.time()) - 3600)},
    )
    assert stale.status_code == 400


def test_completed_checkout_links_subscription_and_stays_pending(client: TestClient) -> None:
    response = _post_event(
        client,
        {
            "id": "evt_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_1",
                    "mode": "subscription",
                    "payment_status": "paid",
                    "client_reference_id": "user_123",
                    "customer": "cus_1",
                    "subscription": "sub_1",
                    "metadata": {"zeus_plan": "monthly"},
                }
            },
        },
    )
    assert response.status_code == 200

    entitlement = client.get("/api/entitlement", headers=_headers()).json()
    assert entitlement["active"] is False
    assert entitlement["plan"] == "monthly"
    assert entitlement["status"] == "pending"

    # The subscription event is the authority for status + period, and the
    # stored subscription id resolves its owner when metadata is absent.
    _post_event(
        client,
        {
            "id": "evt_sub_created",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_1",
                    "customer": "cus_1",
                    "status": "active",
                    "current_period_end": int(time.time()) + 2_592_000,
                }
            },
        },
    )

    entitlement = client.get("/api/entitlement", headers=_headers()).json()
    assert entitlement["active"] is True
    assert entitlement["plan"] == "monthly"
    assert entitlement["status"] == "active"
    assert "constellation" in entitlement["features"]
    assert "agents:5" in entitlement["features"]


def test_late_checkout_event_does_not_downgrade_an_active_subscription(
    client: TestClient,
) -> None:
    _post_event(
        client,
        {
            "id": "evt_sub_first",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_ordered",
                    "customer": "cus_ordered",
                    "status": "active",
                    "current_period_end": int(time.time()) + 2_592_000,
                    "metadata": {
                        "zeus_user_id": "user_ordered",
                        "zeus_plan": "monthly",
                    },
                }
            },
        },
    )
    _post_event(
        client,
        {
            "id": "evt_checkout_late",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_ordered",
                    "mode": "subscription",
                    "payment_status": "paid",
                    "client_reference_id": "user_ordered",
                    "customer": "cus_ordered",
                    "subscription": "sub_ordered",
                    "metadata": {"zeus_plan": "monthly"},
                }
            },
        },
    )

    entitlement = client.get("/api/entitlement", headers=_headers("user_ordered")).json()
    assert entitlement["active"] is True
    assert entitlement["status"] == "active"
    assert entitlement["current_period_end"] is not None


def test_unpaid_checkout_does_not_grant_access(client: TestClient) -> None:
    _post_event(
        client,
        {
            "id": "evt_unpaid",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_unpaid",
                    "mode": "subscription",
                    "payment_status": "unpaid",
                    "client_reference_id": "user_unpaid",
                    "metadata": {"zeus_plan": "monthly"},
                }
            },
        },
    )

    entitlement = client.get("/api/entitlement", headers=_headers("user_unpaid")).json()
    assert entitlement["active"] is False
    assert entitlement["plan"] is None


def test_subscription_created_grants_trial(client: TestClient) -> None:
    period_end = int(time.time()) + 172_800
    _post_event(
        client,
        {
            "id": "evt_trial_checkout",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_trial",
                    "mode": "subscription",
                    "payment_status": "no_payment_required",
                    "client_reference_id": "user_trial",
                    "customer": "cus_trial",
                    "subscription": "sub_trial",
                    "metadata": {"zeus_plan": "annual"},
                }
            },
        },
    )
    _post_event(
        client,
        {
            "id": "evt_trial_sub",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_trial",
                    "customer": "cus_trial",
                    "status": "trialing",
                    "current_period_end": period_end,
                }
            },
        },
    )

    entitlement = client.get("/api/entitlement", headers=_headers("user_trial")).json()
    assert entitlement["active"] is True
    assert entitlement["status"] == "trialing"
    assert entitlement["current_period_end"] == period_end
    assert "agents:10" in entitlement["features"]


def test_cancelled_subscription_revokes_access(client: TestClient) -> None:
    _post_event(
        client,
        {
            "id": "evt_start",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_2",
                    "mode": "subscription",
                    "payment_status": "paid",
                    "client_reference_id": "user_cancel",
                    "subscription": "sub_cancel",
                    "metadata": {"zeus_plan": "monthly"},
                }
            },
        },
    )

    _post_event(
        client,
        {
            "id": "evt_cancel",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_cancel",
                    "customer": "cus_cancel",
                    "status": "canceled",
                    "metadata": {"zeus_user_id": "user_cancel"},
                }
            },
        },
    )

    entitlement = client.get("/api/entitlement", headers=_headers("user_cancel")).json()
    assert entitlement["active"] is False
    assert entitlement["plan"] == "monthly"
    assert entitlement["status"] == "canceled"


def test_subscription_event_resolves_owner_from_stored_subscription(client: TestClient) -> None:
    _post_event(
        client,
        {
            "id": "evt_link",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_link",
                    "mode": "subscription",
                    "payment_status": "paid",
                    "client_reference_id": "user_lookup",
                    "subscription": "sub_lookup",
                    "metadata": {"zeus_plan": "monthly"},
                }
            },
        },
    )

    # Stripe sends subscription events without our user metadata when the
    # checkout session did not exist yet; the stored subscription id is the
    # fallback that keeps the entitlement in sync.
    _post_event(
        client,
        {
            "id": "evt_past_due",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_lookup",
                    "status": "past_due",
                    "current_period_end": int(time.time()) + 86_400,
                }
            },
        },
    )

    entitlement = client.get("/api/entitlement", headers=_headers("user_lookup")).json()
    assert entitlement["active"] is False
    assert entitlement["plan"] == "monthly"
    assert entitlement["status"] == "past_due"


def test_expired_period_revokes_access_but_keeps_the_plan(client: TestClient) -> None:
    client.app.state.store.upsert(
        user_id="user_expired",
        plan="annual",
        status="active",
        current_period_end=int(time.time()) - 60,
    )

    entitlement = client.get("/api/entitlement", headers=_headers("user_expired")).json()
    assert entitlement["active"] is False
    assert entitlement["plan"] == "annual"
    assert entitlement["status"] == "active"
    assert entitlement["features"] == []
