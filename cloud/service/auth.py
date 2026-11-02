"""Clerk session verification for the cloud API."""

from __future__ import annotations

import os
from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException

from .deps import get_settings
from .settings import Settings


@lru_cache(maxsize=8)
def _jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url)


def current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="missing bearer token")

    # Local development only: `ZEUS_CLOUD_DEV_AUTH=1` accepts `dev:<user_id>`.
    # Never with a live key, even if the live-mode startup guard was lifted.
    if os.getenv("ZEUS_CLOUD_DEV_AUTH") == "1" and token.startswith("dev:"):
        if settings.stripe_secret.startswith("sk_live_"):
            raise HTTPException(status_code=403, detail="dev auth is disabled with a live Stripe key")
        user_id = token[4:].strip()
        if user_id:
            return user_id

    if not settings.clerk_frontend_api:
        raise HTTPException(status_code=503, detail="Clerk frontend API is not configured")
    try:
        key = _jwks_client(
            f"https://{settings.clerk_frontend_api}/.well-known/jwks.json"
        ).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except Exception as error:  # jwt raises several subclasses
        raise HTTPException(status_code=401, detail="invalid or expired token") from error

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="token has no subject")
    return str(subject)
