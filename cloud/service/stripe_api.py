"""Minimal Stripe HTTP client and webhook signature verification."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .settings import Settings

API = "https://api.stripe.com/v1"


class StripeError(RuntimeError):
    """Stripe rejected a request; the message is safe to log (no key)."""


def _request(
    secret: str,
    method: str,
    path: str,
    data: dict[str, str] | None = None,
    *,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    if not secret:
        raise StripeError("STRIPE_SECRET_KEY is not configured")
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    request = urllib.request.Request(f"{API}{path}", data=body, method=method)
    request.add_header("Authorization", f"Bearer {secret}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    if idempotency_key:
        request.add_header("Idempotency-Key", idempotency_key)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:500]
        raise StripeError(f"Stripe {method} {path} failed ({error.code}): {detail}") from error
    except urllib.error.URLError as error:
        raise StripeError(f"Stripe {method} {path} unreachable: {error.reason}") from error


def create_checkout_session(
    settings: Settings,
    *,
    user_id: str,
    plan_key: str,
) -> dict[str, Any]:
    plan = settings.plan(plan_key)
    if plan is None:
        raise ValueError(f"unknown plan: {plan_key}")
    payload = {
        "mode": "subscription",
        "line_items[0][price]": str(plan["price_id"]),
        "line_items[0][quantity]": "1",
        "client_reference_id": user_id,
        "metadata[zeus_user_id]": user_id,
        "metadata[zeus_plan]": plan_key,
        # Stripe does not copy Checkout Session metadata onto the subscription.
        # Without these, a subscription.* webhook that arrives before
        # checkout.session.completed cannot identify its owner.
        "subscription_data[metadata][zeus_user_id]": user_id,
        "subscription_data[metadata][zeus_plan]": plan_key,
        "subscription_data[trial_period_days]": str(settings.trial_days),
        "success_url": settings.success_url,
        "cancel_url": settings.cancel_url,
        "allow_promotion_codes": "true",
    }
    return _request(
        settings.stripe_secret,
        "POST",
        "/checkout/sessions",
        payload,
        idempotency_key=f"zeus-checkout-{user_id}-{plan_key}",
    )


def verify_webhook(
    payload: bytes,
    signature_header: str,
    secret: str,
    *,
    tolerance: int = 300,
) -> dict[str, Any]:
    """Verify Stripe's `t=...,v1=...` signature and return the event."""
    if not secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET is not configured")
    pairs = [
        item.split("=", 1)
        for item in (signature_header or "").split(",")
        if "=" in item
    ]
    timestamps = [value for key, value in pairs if key == "t"]
    signatures = [value for key, value in pairs if key == "v1"]
    if not timestamps or not signatures:
        raise ValueError("missing Stripe signature")
    try:
        timestamp = int(timestamps[0])
    except ValueError as error:
        raise ValueError("invalid Stripe signature timestamp") from error
    if abs(time.time() - timestamp) > tolerance:
        raise ValueError("stale Stripe signature")

    signed = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in signatures):
        raise ValueError("invalid Stripe signature")
    return json.loads(payload.decode("utf-8"))
