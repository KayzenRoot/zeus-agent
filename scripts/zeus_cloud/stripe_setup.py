#!/usr/bin/env python3
"""Create the Zeus subscription catalog in Stripe.

The owner authorized these prices (ADR-007):

    mensal      R$  990,00
    trimestral  R$ 2.670,00
    semestral   R$ 5.040,00
    anual       R$ 9.480,00
    trial       2 days (applied by Checkout, not by the Price)

The script is idempotent: it reuses a product whose ``metadata.zeus_plan``
matches and a price whose amount/currency/interval matches. It never prints
the secret key. A live key requires an explicit ``--live``; without it the
script refuses to touch production.

Usage:
    STRIPE_SECRET_KEY=sk_test_... python scripts/zeus_cloud/stripe_setup.py --dry-run
    STRIPE_SECRET_KEY=sk_test_... python scripts/zeus_cloud/stripe_setup.py
    STRIPE_SECRET_KEY=sk_live_... python scripts/zeus_cloud/stripe_setup.py --live
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

API = "https://api.stripe.com/v1"
TRIAL_DAYS = 2
CURRENCY = "brl"


@dataclass(frozen=True)
class Plan:
    key: str
    name: str
    amount: int  # cents
    interval: str
    interval_count: int


PLANS: tuple[Plan, ...] = (
    Plan("monthly", "Zeus Pro - Mensal", 99000, "month", 1),
    Plan("quarterly", "Zeus Pro - Trimestral", 267000, "month", 3),
    Plan("semiannual", "Zeus Pro - Semestral", 504000, "month", 6),
    Plan("annual", "Zeus Pro - Anual", 948000, "month", 12),
)


def _request(
    secret: str,
    method: str,
    path: str,
    *,
    data: Optional[dict[str, str]] = None,
    idempotency_key: Optional[str] = None,
) -> dict[str, Any]:
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
        detail = error.read().decode("utf-8", "replace")[:800]
        raise SystemExit(f"Stripe {method} {path} failed ({error.code}): {detail}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Stripe {method} {path} unreachable: {error.reason}") from error


def _list_all(secret: str, path: str) -> list[dict[str, Any]]:
    """List active objects; the catalog is small, so one page is enough."""
    separator = "&" if "?" in path else "?"
    payload = _request(secret, "GET", f"{path}{separator}limit=100")
    return list(payload.get("data") or [])


def _find_product(secret: str, plan: Plan) -> Optional[dict[str, Any]]:
    for product in _list_all(secret, "/products?active=true"):
        if (product.get("metadata") or {}).get("zeus_plan") == plan.key:
            return product
    return None


def _ensure_product(secret: str, plan: Plan, *, dry_run: bool) -> dict[str, Any]:
    existing = None if dry_run else _find_product(secret, plan)
    if existing:
        return existing
    payload = {
        "name": plan.name,
        "description": f"Zeus Agent - plano {plan.name.removeprefix('Zeus Pro - ')}",
        "metadata[zeus_plan]": plan.key,
        "metadata[trial_period_days]": str(TRIAL_DAYS),
    }
    if dry_run:
        return {"id": f"dry_product_{plan.key}", "payload": payload}
    return _request(
        secret,
        "POST",
        "/products",
        data=payload,
        idempotency_key=f"zeus-product-{plan.key}",
    )


def _price_matches(price: dict[str, Any], plan: Plan) -> bool:
    recurring = price.get("recurring") or {}
    return (
        price.get("active") is True
        and price.get("currency") == CURRENCY
        and price.get("unit_amount") == plan.amount
        and recurring.get("interval") == plan.interval
        and recurring.get("interval_count") == plan.interval_count
    )


def _ensure_price(
    secret: str,
    product_id: str,
    plan: Plan,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    if not dry_run:
        for price in _list_all(secret, f"/prices?product={urllib.parse.quote(product_id)}&active=true"):
            if _price_matches(price, plan):
                return price
    payload = {
        "product": product_id,
        "currency": CURRENCY,
        "unit_amount": str(plan.amount),
        "recurring[interval]": plan.interval,
        "recurring[interval_count]": str(plan.interval_count),
        "nickname": plan.name,
        "metadata[zeus_plan]": plan.key,
    }
    if dry_run:
        return {"id": f"dry_price_{plan.key}", "payload": payload}
    return _request(
        secret,
        "POST",
        "/prices",
        data=payload,
        idempotency_key=f"zeus-price-{plan.key}-{plan.amount}",
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print payloads, no network")
    parser.add_argument("--live", action="store_true", help="required for an sk_live_ key")
    parser.add_argument("--out", help="write the price-id map to this JSON file")
    args = parser.parse_args(argv)

    secret = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not secret and not args.dry_run:
        print("STRIPE_SECRET_KEY is not set", file=sys.stderr)
        return 2
    if secret.startswith("sk_live_") and not args.live:
        print("Refusing a live key without --live", file=sys.stderr)
        return 2
    if args.dry_run and not secret:
        secret = "sk_test_dry_run"

    catalog: dict[str, Any] = {
        "currency": CURRENCY,
        "trial_period_days": TRIAL_DAYS,
        "mode": "live" if secret.startswith("sk_live_") else "test",
        "plans": {},
    }
    for plan in PLANS:
        product = _ensure_product(secret, plan, dry_run=args.dry_run)
        price = _ensure_price(secret, product["id"], plan, dry_run=args.dry_run)
        catalog["plans"][plan.key] = {
            "product_id": product["id"],
            "price_id": price["id"],
            "amount": plan.amount,
            "interval": plan.interval,
            "interval_count": plan.interval_count,
            "name": plan.name,
        }
        print(f"{plan.key}: {price['id']}", file=sys.stderr)

    text = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
