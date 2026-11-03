"""Zeus Cloud control plane: Clerk-authenticated checkout + Stripe entitlements."""

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import stripe_api
from .auth import current_user
from .entitlements import (
    EntitlementNotConfigured,
    is_active,
    plan_features,
    sign_entitlement,
)
from .settings import Settings
from .store import EntitlementStore


class CheckoutRequest(BaseModel):
    plan: str


class TokenRequest(BaseModel):
    device_id: str = Field(min_length=8, max_length=128)


class DeviceAuthorizeRequest(BaseModel):
    device_id: str = Field(min_length=8, max_length=128)


class DeviceExchangeRequest(BaseModel):
    code: str = Field(min_length=16, max_length=256)
    device_id: str = Field(min_length=8, max_length=128)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.assert_startup_safe()
    store = EntitlementStore(settings.db_path)
    app = FastAPI(title="Zeus Cloud", version="0.1.0")
    app.state.settings = settings
    app.state.store = store
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.allowed_origins),
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "service": "zeus-cloud",
            "mode": "live" if settings.stripe_secret.startswith("sk_live_") else "test",
        }

    @app.get("/api/plans")
    def public_plans() -> dict[str, Any]:
        return settings.plans()

    @app.post("/api/checkout")
    def checkout(
        body: CheckoutRequest,
        user: str = Depends(current_user),
    ) -> dict[str, Any]:
        try:
            session = stripe_api.create_checkout_session(
                settings,
                user_id=user,
                plan_key=body.plan,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except stripe_api.StripeError as error:
            raise HTTPException(status_code=502, detail="checkout unavailable") from error
        url = session.get("url")
        if not url:
            raise HTTPException(status_code=502, detail="Stripe returned no checkout URL")
        return {"url": url, "id": session.get("id")}

    @app.get("/api/entitlement")
    def entitlement(user: str = Depends(current_user)) -> dict[str, Any]:
        row = store.get(user)
        current_period_end = int(row["current_period_end"]) if row and row["current_period_end"] else None
        active = is_active(row)
        return {
            "active": active,
            "plan": row["plan"] if row else None,
            "status": row["status"] if row else "inactive",
            "current_period_end": current_period_end,
            "features": plan_features(row["plan"]) if row and active else [],
        }

    @app.post("/api/entitlement/token")
    def entitlement_token(
        body: TokenRequest,
        user: str = Depends(current_user),
    ) -> dict[str, Any]:
        row = store.get(user)
        if not is_active(row):
            raise HTTPException(status_code=403, detail="no active subscription")
        try:
            return sign_entitlement(settings, row, device_id=body.device_id)
        except EntitlementNotConfigured as error:
            raise HTTPException(status_code=503, detail="entitlement signing is not configured") from error

    @app.post("/api/device/authorize")
    def authorize_device(
        body: DeviceAuthorizeRequest,
        user: str = Depends(current_user),
    ) -> dict[str, Any]:
        if not is_active(store.get(user)):
            raise HTTPException(status_code=403, detail="no active subscription")
        code = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + 600
        store.create_device_code(
            code_hash=hashlib.sha256(code.encode()).hexdigest(),
            user_id=user,
            device_id=body.device_id,
            expires_at=expires_at,
        )
        return {"code": code, "expires_at": expires_at}

    @app.post("/api/device/exchange")
    def exchange_device(body: DeviceExchangeRequest) -> dict[str, Any]:
        now = int(time.time())
        code_row = store.consume_device_code(
            code_hash=hashlib.sha256(body.code.encode()).hexdigest(),
            device_id=body.device_id,
            now=now,
        )
        if code_row is None:
            raise HTTPException(status_code=400, detail="invalid or expired activation code")
        row = store.get(str(code_row["user_id"]))
        if not is_active(row, now=now):
            raise HTTPException(status_code=403, detail="no active subscription")
        try:
            return sign_entitlement(settings, row, device_id=body.device_id, now=now)
        except EntitlementNotConfigured as error:
            raise HTTPException(status_code=503, detail="entitlement signing is not configured") from error

    @app.post("/api/stripe/webhook")
    async def stripe_webhook(request: Request) -> dict[str, bool]:
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")
        try:
            event = stripe_api.verify_webhook(
                payload,
                signature,
                settings.stripe_webhook_secret,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        _apply_event(event, settings, store)
        return {"received": True}

    return app


def _first_price(obj: dict[str, Any]) -> str | None:
    items = (obj.get("items") or {}).get("data") or []
    if not items:
        return None
    price = (items[0] or {}).get("price") or {}
    return price.get("id")


def _apply_event(event: dict[str, Any], settings: Settings, store: EntitlementStore) -> None:
    event_type = str(event.get("type") or "")
    obj = (event.get("data") or {}).get("object") or {}
    if event_type == "checkout.session.completed":
        _checkout_completed(obj, settings, store)
    elif event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        _subscription_changed(event_type, obj, settings, store)


def _checkout_completed(
    session: dict[str, Any],
    settings: Settings,
    store: EntitlementStore,
) -> None:
    metadata = session.get("metadata") or {}
    user_id = session.get("client_reference_id") or metadata.get("zeus_user_id")
    plan = metadata.get("zeus_plan") or settings.plan_for_price(_first_price(session) or "")
    if not user_id or not plan:
        return
    mode = str(session.get("mode") or "")
    if mode and mode != "subscription":
        return
    payment_status = str(session.get("payment_status") or "")
    if payment_status and payment_status not in {"paid", "no_payment_required"}:
        return

    subscription_id = session.get("subscription")
    # The authoritative status and period come from customer.subscription.*,
    # whose object is delivered by Stripe. Never fetch by an ID taken from a
    # webhook body: that is an SSRF sink and an unnecessary trust hop.
    if store.get(str(user_id)) is None:
        store.upsert(
            user_id=str(user_id),
            plan=str(plan),
            status="pending",
            customer_id=session.get("customer"),
            subscription_id=str(subscription_id) if subscription_id else None,
            current_period_end=None,
        )
    else:
        # A subscription event may have arrived first; only attach the ids.
        store.link(
            user_id=str(user_id),
            customer_id=session.get("customer"),
            subscription_id=str(subscription_id) if subscription_id else None,
        )


def _subscription_changed(
    event_type: str,
    subscription: dict[str, Any],
    settings: Settings,
    store: EntitlementStore,
) -> None:
    metadata = subscription.get("metadata") or {}
    subscription_id = subscription.get("id")
    user_id = metadata.get("zeus_user_id")
    row = store.get(str(user_id)) if user_id else None
    if row is None and subscription_id:
        row = store.find_by_subscription(str(subscription_id))
    if not user_id and row:
        user_id = row["user_id"]
    plan = (
        metadata.get("zeus_plan")
        or (row["plan"] if row else None)
        or settings.plan_for_price(_first_price(subscription) or "")
    )
    if not user_id or not plan:
        return

    status = "canceled" if event_type == "customer.subscription.deleted" else str(
        subscription.get("status") or "inactive"
    )
    store.upsert(
        user_id=str(user_id),
        plan=str(plan),
        status=status,
        customer_id=subscription.get("customer"),
        subscription_id=str(subscription_id) if subscription_id else None,
        current_period_end=(
            int(subscription["current_period_end"])
            if subscription.get("current_period_end")
            else None
        ),
    )
