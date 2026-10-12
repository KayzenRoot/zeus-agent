# Architecture
Base: unchanged NousResearch/hermes-agent code from pinned upstream Git commit.
Existing upstream dashboard: `hermes_cli/web_server.py`, `hermes_cli/web_routers/`, `web/src/` using `apps/shared`, PTY bridge for Ink TUI. Respect upstream `web/AGENTS.md`: do NOT build a duplicate chat UI; extend adjacent React inspectors/panels. POSIX PTY requires WSL2 on Windows.
Zeus-specific logic should be thin overlays/theme/custom assets; preserve CLI/package/protocol keys until compatibility tests prove a migration safe. Future agents activity feed must be emitted as structured, redacted, authenticated events with bounded retention and optional browser subscription.
`upstream` remote sync is a controlled Git operation on local machine only, never automatic blind merge.
