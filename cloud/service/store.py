"""SQLite entitlement store for the Zeus Cloud control plane."""

from __future__ import annotations

import sqlite3
import json
import time
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS entitlements (
    user_id TEXT PRIMARY KEY,
    org_id TEXT,
    plan TEXT NOT NULL,
    status TEXT NOT NULL,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    current_period_end INTEGER,
    updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS entitlements_subscription
    ON entitlements (stripe_subscription_id);
CREATE TABLE IF NOT EXISTS device_codes (
    code_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    used_at INTEGER,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS device_codes_user
    ON device_codes (user_id);
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    org_id TEXT,
    name TEXT,
    created_at INTEGER NOT NULL,
    last_seen INTEGER NOT NULL,
    revoked_at INTEGER
);
CREATE INDEX IF NOT EXISTS devices_user
    ON devices (user_id);
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    org_id TEXT,
    event TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS audit_events_user
    ON audit_events (user_id, created_at);
"""


class EntitlementStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            self._ensure_column(connection, "entitlements", "org_id", "TEXT")
            self._ensure_column(connection, "devices", "org_id", "TEXT")
            self._ensure_column(connection, "audit_events", "org_id", "TEXT")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS entitlements_org ON entitlements (org_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS devices_org ON devices (org_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS audit_events_org ON audit_events (org_id, created_at)"
            )

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection, table: str, column: str, declaration: str
    ) -> None:
        columns = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def upsert(
        self,
        *,
        user_id: str,
        plan: str,
        status: str,
        customer_id: str | None = None,
        subscription_id: str | None = None,
        current_period_end: int | None = None,
        org_id: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO entitlements (
                    user_id, org_id, plan, status, stripe_customer_id,
                    stripe_subscription_id, current_period_end, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    org_id = COALESCE(excluded.org_id, entitlements.org_id),
                    plan = excluded.plan,
                    status = excluded.status,
                    stripe_customer_id = COALESCE(excluded.stripe_customer_id, entitlements.stripe_customer_id),
                    stripe_subscription_id = COALESCE(excluded.stripe_subscription_id, entitlements.stripe_subscription_id),
                    current_period_end = COALESCE(excluded.current_period_end, entitlements.current_period_end),
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    org_id,
                    plan,
                    status,
                    customer_id,
                    subscription_id,
                    current_period_end,
                    int(time.time()),
                ),
            )

    def get(self, user_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM entitlements WHERE user_id = ?", (user_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_for_identity(self, user_id: str, org_id: str | None) -> dict[str, Any] | None:
        if org_id:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM entitlements WHERE org_id = ? ORDER BY updated_at DESC LIMIT 1",
                    (org_id,),
                ).fetchone()
            if row:
                return dict(row)
        return self.get(user_id)

    def link(
        self,
        *,
        user_id: str,
        customer_id: str | None,
        subscription_id: str | None,
        org_id: str | None = None,
    ) -> None:
        """Attach Stripe ids without touching an existing plan/status/period."""
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE entitlements SET
                    org_id = COALESCE(?, org_id),
                    stripe_customer_id = COALESCE(?, stripe_customer_id),
                    stripe_subscription_id = COALESCE(?, stripe_subscription_id),
                    updated_at = ?
                WHERE user_id = ?
                """,
                (org_id, customer_id, subscription_id, int(time.time()), user_id),
            )

    def find_by_subscription(self, subscription_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM entitlements WHERE stripe_subscription_id = ?",
                (subscription_id,),
            ).fetchone()
        return dict(row) if row else None

    def create_device_code(
        self,
        *,
        code_hash: str,
        user_id: str,
        device_id: str,
        expires_at: int,
    ) -> None:
        now = int(time.time())
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM device_codes WHERE expires_at < ?", (now - 3600,)
            )
            connection.execute(
                """
                INSERT INTO device_codes (
                    code_hash, user_id, device_id, expires_at, used_at, created_at
                ) VALUES (?, ?, ?, ?, NULL, ?)
                """,
                (code_hash, user_id, device_id, expires_at, now),
            )

    def consume_device_code(
        self,
        *,
        code_hash: str,
        device_id: str,
        now: int,
    ) -> dict[str, Any] | None:
        """Atomically burn a code; wrong device, expiry and reuse all fail closed."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM device_codes WHERE code_hash = ?", (code_hash,)
            ).fetchone()
            if (
                row is None
                or row["used_at"] is not None
                or int(row["expires_at"]) <= now
                or row["device_id"] != device_id
            ):
                return None
            cursor = connection.execute(
                "UPDATE device_codes SET used_at = ? WHERE code_hash = ? AND used_at IS NULL",
                (now, code_hash),
            )
            if cursor.rowcount != 1:
                return None
            return dict(row)

    def upsert_device(
        self,
        *,
        device_id: str,
        user_id: str,
        name: str | None,
        org_id: str | None = None,
    ) -> bool:
        """Register a device; refuse a device id already owned by another account."""
        now = int(time.time())
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT user_id, org_id FROM devices WHERE device_id = ?", (device_id,)
            ).fetchone()
            if (
                existing is not None
                and existing["user_id"] != user_id
                and (not org_id or existing["org_id"] != org_id)
            ):
                return False
            connection.execute(
                """
                INSERT INTO devices (device_id, user_id, org_id, name, created_at, last_seen, revoked_at)
                VALUES (?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(device_id) DO UPDATE SET
                    org_id = COALESCE(excluded.org_id, devices.org_id),
                    name = COALESCE(excluded.name, devices.name),
                    last_seen = excluded.last_seen
                """,
                (device_id, user_id, org_id, name, now, now),
            )
            return True

    def list_devices(self, user_id: str, org_id: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as connection:
            if org_id:
                rows = connection.execute(
                    "SELECT * FROM devices WHERE org_id = ? ORDER BY last_seen DESC",
                    (org_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM devices WHERE user_id = ? ORDER BY last_seen DESC",
                    (user_id,),
                ).fetchall()
        return [dict(row) for row in rows]

    def revoke_device(
        self, *, user_id: str, device_id: str, org_id: str | None = None
    ) -> bool:
        with self._connect() as connection:
            if org_id:
                cursor = connection.execute(
                    "UPDATE devices SET revoked_at = ? WHERE org_id = ? AND device_id = ? AND revoked_at IS NULL",
                    (int(time.time()), org_id, device_id),
                )
            else:
                cursor = connection.execute(
                    "UPDATE devices SET revoked_at = ? WHERE user_id = ? AND device_id = ? AND revoked_at IS NULL",
                    (int(time.time()), user_id, device_id),
                )
            return cursor.rowcount == 1

    def device_revoked(self, device_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT revoked_at FROM devices WHERE device_id = ?", (device_id,)
            ).fetchone()
        return bool(row and row["revoked_at"] is not None)

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM devices WHERE device_id = ?", (device_id,)
            ).fetchone()
        return dict(row) if row else None

    def count_active_devices(self, user_id: str, org_id: str | None = None) -> int:
        with self._connect() as connection:
            if org_id:
                row = connection.execute(
                    "SELECT COUNT(*) FROM devices WHERE org_id = ? AND revoked_at IS NULL",
                    (org_id,),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) FROM devices WHERE user_id = ? AND revoked_at IS NULL",
                    (user_id,),
                ).fetchone()
        return int(row[0]) if row else 0

    def audit(
        self,
        *,
        user_id: str,
        event: str,
        detail: dict[str, Any],
        org_id: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO audit_events (user_id, org_id, event, detail, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, org_id, event, json.dumps(detail, ensure_ascii=False), int(time.time())),
            )

    def list_audit(
        self, user_id: str, *, limit: int = 50, org_id: str | None = None
    ) -> list[dict[str, Any]]:
        with self._connect() as connection:
            if org_id:
                rows = connection.execute(
                    "SELECT id, event, detail, created_at FROM audit_events "
                    "WHERE org_id = ? ORDER BY id DESC LIMIT ?",
                    (org_id, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT id, event, detail, created_at FROM audit_events "
                    "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                    (user_id, limit),
                ).fetchall()
        events = []
        for row in rows:
            try:
                detail = json.loads(row["detail"])
            except ValueError:
                detail = {}
            events.append(
                {
                    "id": int(row["id"]),
                    "event": row["event"],
                    "detail": detail if isinstance(detail, dict) else {},
                    "created_at": int(row["created_at"]),
                }
            )
        return events
