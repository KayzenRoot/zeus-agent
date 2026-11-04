"""Zeus Cloud control plane: Clerk-authenticated checkout + Stripe entitlements."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import secrets
import sqlite3
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import stripe_api
from .auth import Identity, current_identity
from .entitlements import (
    FEATURES,
    EntitlementNotConfigured,
    is_active,
    plan_features,
    plan_seats,
    sign_entitlement,
    signing_key_configured,
)
from .settings import Settings
from .store import EntitlementStore


class CheckoutRequest(BaseModel):
    plan: str


class TokenRequest(BaseModel):
    device_id: str = Field(min_length=8, max_length=128)


class DeviceAuthorizeRequest(BaseModel):
    device_id: str = Field(min_length=8, max_length=128)
    device_name: str = Field(default="", max_length=64)


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
            "mode": _stripe_mode(settings),
        }

    @app.get("/api/readiness")
    def readiness() -> dict[str, Any]:
        checks = {
            "stripe": bool(settings.stripe_secret),
            "stripe_webhook": bool(settings.stripe_webhook_secret),
            "clerk": bool(settings.clerk_frontend_api),
            "entitlement_signing": signing_key_configured(settings)
            and settings.entitlement_ttl_days > 0,
            "plans": _plans_configured(settings),
            "database": _database_ready(store),
        }
        return {
            "ready": all(checks.values()),
            "checks": checks,
            "mode": _stripe_mode(settings),
        }

    @app.get("/api/plans")
    def public_plans() -> dict[str, Any]:
        return settings.plans()

    @app.get("/api/identity")
    def identity(identity: Identity = Depends(current_identity)) -> dict[str, Any]:
        return {
            "user_id": identity.user_id,
            "org_id": identity.org_id,
            "org_role": identity.org_role,
        }

    @app.post("/api/checkout")
    def checkout(
        body: CheckoutRequest,
        identity: Identity = Depends(current_identity),
    ) -> dict[str, Any]:
        user = identity.user_id
        if identity.org_id and identity.org_role not in {"org:admin", "org:owner"}:
            raise HTTPException(status_code=403, detail="organization admin required")
        try:
            session = stripe_api.create_checkout_session(
                settings,
                user_id=user,
                plan_key=body.plan,
                org_id=identity.org_id,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except stripe_api.StripeError as error:
            raise HTTPException(status_code=502, detail="checkout unavailable") from error
        url = session.get("url")
        if not url:
            raise HTTPException(status_code=502, detail="Stripe returned no checkout URL")
        store.audit(
            user_id=user,
            org_id=identity.org_id,
            event="checkout.created",
            detail={"plan": body.plan},
        )
        return {"url": url, "id": session.get("id")}

    @app.get("/api/entitlement")
    def entitlement(identity: Identity = Depends(current_identity)) -> dict[str, Any]:
        row = store.get_for_identity(identity.user_id, identity.org_id)
        current_period_end = int(row["current_period_end"]) if row and row["current_period_end"] else None
        active = is_active(row)
        scope = "organization" if identity.org_id and row and row.get("org_id") else "user"
        return {
            "active": active,
            "plan": row["plan"] if row else None,
            "status": row["status"] if row else "inactive",
            "current_period_end": current_period_end,
            "seats": plan_seats(row["plan"]) if row and active else 0,
            "features": plan_features(row["plan"]) if row and active else [],
            "scope": scope,
        }

    @app.post("/api/billing/portal")
    def billing_portal(identity: Identity = Depends(current_identity)) -> dict[str, Any]:
        user = identity.user_id
        if identity.org_id and identity.org_role not in {"org:admin", "org:owner"}:
            raise HTTPException(status_code=403, detail="organization admin required")
        row = store.get_for_identity(user, identity.org_id)
        if not is_active(row):
            raise HTTPException(status_code=403, detail="no active subscription")
        customer_id = row.get("stripe_customer_id") if row else None
        if not customer_id:
            raise HTTPException(status_code=404, detail="no Stripe customer for this account")
        try:
            session = stripe_api.create_billing_portal_session(
                settings,
                customer_id=str(customer_id),
                return_url=settings.portal_return_url,
            )
        except stripe_api.StripeError as error:
            raise HTTPException(status_code=502, detail="billing portal unavailable") from error
        url = session.get("url")
        if not url:
            raise HTTPException(status_code=502, detail="Stripe returned no portal URL")
        store.audit(
            user_id=user,
            org_id=identity.org_id,
            event="billing.portal",
            detail={"customer_id": str(customer_id)},
        )
        return {"url": url}

    @app.post("/api/entitlement/token")
    def entitlement_token(
        body: TokenRequest,
        identity: Identity = Depends(current_identity),
    ) -> dict[str, Any]:
        row = store.get_for_identity(identity.user_id, identity.org_id)
        if not is_active(row):
            raise HTTPException(status_code=403, detail="no active subscription")
        if store.device_revoked(body.device_id):
            raise HTTPException(status_code=403, detail="device is revoked")
        try:
            return sign_entitlement(settings, row, device_id=body.device_id)
        except EntitlementNotConfigured as error:
            raise HTTPException(status_code=503, detail="entitlement signing is not configured") from error

    @app.post("/api/device/authorize")
    def authorize_device(
        body: DeviceAuthorizeRequest,
        identity: Identity = Depends(current_identity),
    ) -> dict[str, Any]:
        user = identity.user_id
        row = store.get_for_identity(user, identity.org_id)
        if not is_active(row):
            raise HTTPException(status_code=403, detail="no active subscription")
        scope_org = str(row["org_id"]) if row and row.get("org_id") else None
        existing = store.get_device(body.device_id)
        if existing is not None and existing["user_id"] != user and existing.get("org_id") != scope_org:
            raise HTTPException(status_code=409, detail="device belongs to another account")
        if existing is not None and existing["revoked_at"] is not None:
            raise HTTPException(status_code=403, detail="device is revoked")
        if existing is None and store.count_active_devices(user, scope_org) >= plan_seats(row["plan"]):
            raise HTTPException(status_code=409, detail="seat limit reached")
        if not store.upsert_device(
            device_id=body.device_id,
            user_id=user,
            name=body.device_name.strip() or None,
            org_id=scope_org,
        ):
            raise HTTPException(status_code=409, detail="device belongs to another account")
        code = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + 600
        store.create_device_code(
            code_hash=hashlib.sha256(code.encode()).hexdigest(),
            user_id=user,
            device_id=body.device_id,
            expires_at=expires_at,
            org_id=scope_org,
        )
        store.audit(
            user_id=user,
            org_id=scope_org,
            event="device.authorize",
            detail={"device_id": body.device_id, "name": body.device_name.strip() or None},
        )
        return {"code": code, "expires_at": expires_at}

    @app.get("/api/devices")
    def devices(identity: Identity = Depends(current_identity)) -> list[dict[str, Any]]:
        return [
            {
                "device_id": row["device_id"],
                "name": row["name"],
                "created_at": int(row["created_at"]),
                "last_seen": int(row["last_seen"]),
                "revoked": row["revoked_at"] is not None,
            }
            for row in store.list_devices(identity.user_id, identity.org_id)
        ]

    @app.post("/api/devices/{device_id}/revoke")
    def revoke_device(
        device_id: str = Path(min_length=8, max_length=128),
        identity: Identity = Depends(current_identity),
    ) -> dict[str, bool]:
        if identity.org_id and identity.org_role not in {"org:admin", "org:owner"}:
            raise HTTPException(status_code=403, detail="organization admin required")
        if not store.revoke_device(
            user_id=identity.user_id, device_id=device_id, org_id=identity.org_id
        ):
            raise HTTPException(status_code=404, detail="device not found")
        store.audit(
            user_id=identity.user_id,
            org_id=identity.org_id,
            event="device.revoke",
            detail={"device_id": device_id},
        )
        return {"revoked": True}

    @app.get("/api/audit")
    def audit(
        limit: int = Query(default=50, ge=1, le=100),
        identity: Identity = Depends(current_identity),
    ) -> dict[str, Any]:
        return {
            "events": store.list_audit(
                identity.user_id, limit=limit, org_id=identity.org_id
            )
        }

    @app.get("/api/audit/export")
    def export_audit(
        format: str = Query(default="json", pattern="^(json|csv)$"),
        limit: int = Query(default=100, ge=1, le=100),
        identity: Identity = Depends(current_identity),
    ) -> Response:
        events = store.list_audit(
            identity.user_id, limit=limit, org_id=identity.org_id
        )
        if format == "csv":
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["id", "event", "created_at", "detail"])
            for event in events:
                writer.writerow(
                    [
                        event["id"],
                        event["event"],
                        event["created_at"],
                        json.dumps(event["detail"], ensure_ascii=False),
                    ]
                )
            return Response(
                content=buffer.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": 'attachment; filename="zeus-audit.csv"'},
            )
        return Response(
            content=json.dumps({"events": events}, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="zeus-audit.json"'},
        )

    @app.post("/api/device/exchange")
    def exchange_device(body: DeviceExchangeRequest) -> dict[str, Any]:
        now = int(time.time())
        if store.device_revoked(body.device_id):
            raise HTTPException(status_code=403, detail="device is revoked")
        code_row = store.consume_device_code(
            code_hash=hashlib.sha256(body.code.encode()).hexdigest(),
            device_id=body.device_id,
            now=now,
        )
        if code_row is None:
            raise HTTPException(status_code=400, detail="invalid or expired activation code")
        user_id = str(code_row["user_id"])
        org_id = str(code_row["org_id"]) if code_row["org_id"] else None
        row = store.get_for_identity(user_id, org_id)
        if not is_active(row, now=now):
            raise HTTPException(status_code=403, detail="no active subscription")
        try:
            token = sign_entitlement(settings, row, device_id=body.device_id, now=now)
        except EntitlementNotConfigured as error:
            raise HTTPException(status_code=503, detail="entitlement signing is not configured") from error
        store.audit(
            user_id=user_id,
            org_id=org_id,
            event="device.exchange",
            detail={"device_id": body.device_id},
        )
        return token

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


def _stripe_mode(settings: Settings) -> str:
    return "live" if settings.stripe_secret.startswith("sk_live_") else "test"


def _plans_configured(settings: Settings) -> bool:
    try:
        plans = settings.plans().get("plans") or {}
    except (OSError, ValueError):
        return False
    return all(
        isinstance(plans.get(key), dict) and str(plans[key].get("price_id") or "").strip()
        for key in FEATURES
    )


def _database_ready(store: EntitlementStore) -> bool:
    try:
        return store.ping()
    except sqlite3.Error:
        return False


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
    org_id = metadata.get("zeus_org_id")
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
    if store.get_for_identity(str(user_id), str(org_id) if org_id else None) is None:
        store.upsert(
            user_id=str(user_id),
            org_id=str(org_id) if org_id else None,
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
            org_id=str(org_id) if org_id else None,
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
    org_id = metadata.get("zeus_org_id")
    row = store.get_for_identity(str(user_id), str(org_id) if org_id else None) if user_id else None
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
        org_id=str(org_id) if org_id else None,
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
