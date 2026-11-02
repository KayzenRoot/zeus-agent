"""Behaviour contracts for the Zeus Cloud checkout and entitlement API."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from cloud.service.app import create_app
from cloud.service import stripe_api
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


def test_completed_checkout_grants_the_plan(client: TestClient) -> None:
    response = _post_event(
        client,
        {
            "id": "evt_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_1",
                    "client_reference_id": "user_123",
                    "customer": "cus_1",
                    "subscription": None,
                    "metadata": {"zeus_plan": "monthly"},
                }
            },
        },
    )
    assert response.status_code == 200

    entitlement = client.get("/api/entitlement", headers=_headers()).json()
    assert entitlement["active"] is True
    assert entitlement["plan"] == "monthly"
    assert entitlement["status"] == "active"
    assert "constellation" in entitlement["features"]
    assert "agents:5" in entitlement["features"]


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


def test_checkout_reads_trial_state_from_stripe(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    period_end = int(time.time()) + 172_800
    monkeypatch.setattr(
        "cloud.service.app.stripe_api.fetch_subscription",
        lambda _settings, subscription_id: {
            "id": subscription_id,
            "status": "trialing",
            "current_period_end": period_end,
        },
    )

    _post_event(
        client,
        {
            "id": "evt_trial",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_trial",
                    "client_reference_id": "user_trial",
                    "customer": "cus_trial",
                    "subscription": "sub_trial",
                    "metadata": {"zeus_plan": "annual"},
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
                    "client_reference_id": "user_cancel",
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


def test_subscription_fetch_failure_fails_closed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unreachable(_settings: Settings, _subscription_id: str) -> dict[str, Any]:
        raise stripe_api.StripeError("temporary Stripe failure")

    monkeypatch.setattr("cloud.service.app.stripe_api.fetch_subscription", unreachable)

    _post_event(
        client,
        {
            "id": "evt_fetch_fail",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_fetch_fail",
                    "mode": "subscription",
                    "payment_status": "paid",
                    "client_reference_id": "user_fetch_fail",
                    "subscription": "sub_fetch_fail",
                    "metadata": {"zeus_plan": "monthly"},
                }
            },
        },
    )

    entitlement = client.get("/api/entitlement", headers=_headers("user_fetch_fail")).json()
    assert entitlement["active"] is False
    assert entitlement["plan"] == "monthly"
    assert entitlement["status"] == "pending"


def test_subscription_event_resolves_owner_from_stored_subscription(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "cloud.service.app.stripe_api.fetch_subscription",
        lambda _settings, subscription_id: {
            "id": subscription_id,
            "status": "active",
            "current_period_end": int(time.time()) + 86_400,
        },
    )
    _post_event(
        client,
        {
            "id": "evt_link",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_link",
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
