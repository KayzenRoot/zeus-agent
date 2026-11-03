"""Configuration for the Zeus Cloud control plane (Clerk + Stripe)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_FRONTEND_API = "adequate-viper-3823.clerk.accounts.dev"
DEFAULT_ORIGINS = "http://127.0.0.1:9120,http://localhost:9120"


@dataclass(frozen=True)
class Settings:
    stripe_secret: str
    stripe_webhook_secret: str
    clerk_frontend_api: str
    db_path: Path
    plans_path: Path
    success_url: str
    cancel_url: str
    trial_days: int = 2
    allowed_origins: tuple[str, ...] = ()
    entitlement_private_key_b64: str = ""
    entitlement_ttl_days: int = 7

    @classmethod
    def from_env(cls) -> Settings:
        root = Path(__file__).resolve().parents[1]
        plans_path = Path(os.getenv("ZEUS_CLOUD_PLANS_FILE", str(root / "plans.json")))
        db_path = Path(os.getenv("ZEUS_CLOUD_DB", str(Path.home() / ".zeus-cloud" / "entitlements.db")))
        origins = tuple(
            origin.strip()
            for origin in os.getenv("ZEUS_CLOUD_ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
            if origin.strip()
        )
        return cls(
            stripe_secret=os.getenv("STRIPE_SECRET_KEY", "").strip(),
            stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", "").strip(),
            clerk_frontend_api=os.getenv("CLERK_FRONTEND_API", DEFAULT_FRONTEND_API).strip().removeprefix("https://").rstrip("/"),
            db_path=db_path,
            plans_path=plans_path,
            success_url=os.getenv("ZEUS_CLOUD_SUCCESS_URL", "http://127.0.0.1:9120/?checkout=success"),
            cancel_url=os.getenv("ZEUS_CLOUD_CANCEL_URL", "http://127.0.0.1:9120/?checkout=cancel"),
            trial_days=int(os.getenv("ZEUS_CLOUD_TRIAL_DAYS", "2")),
            allowed_origins=origins,
            entitlement_private_key_b64=os.getenv("ZEUS_ENTITLEMENT_PRIVATE_KEY_B64", "").strip(),
            entitlement_ttl_days=int(os.getenv("ZEUS_ENTITLEMENT_TTL_DAYS", "7")),
        )

    def plans(self) -> dict[str, Any]:
        return json.loads(self.plans_path.read_text(encoding="utf-8"))

    def plan(self, key: str) -> dict[str, Any] | None:
        plans = self.plans().get("plans") or {}
        value = plans.get(key)
        return value if isinstance(value, dict) else None

    def plan_for_price(self, price_id: str) -> str | None:
        for key, plan in (self.plans().get("plans") or {}).items():
            if isinstance(plan, dict) and plan.get("price_id") == price_id:
                return key
        return None

    def assert_startup_safe(self) -> None:
        """Live keys would move real money; they need an explicit owner go-live."""
        if self.stripe_secret.startswith("sk_live_") and os.getenv("ZEUS_CLOUD_ALLOW_LIVE") != "1":
            raise RuntimeError(
                "refusing live Stripe key: set ZEUS_CLOUD_ALLOW_LIVE=1 after the owner-approved go-live"
            )
