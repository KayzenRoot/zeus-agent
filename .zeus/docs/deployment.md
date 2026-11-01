# Deployment
Phase 1: Windows workstation with WSL2 recommended, local dev ports only. Preserve a clean source checkout and local environment secrets outside Git.
VPS: NOT AUTHORIZED / out of current scope. Future deployment needs independent local pass, backup/rollback, secret management, protected access, observability, and explicit owner go-ahead.

## Phase 2 (2026-11-01): VPS deployment target authorized (ADR-006)
- Target: owner's existing Amazon Linux VPS. Deployment kit: `.zeus/docs/deployment-vps.md` (Docker compose from the Zeus checkout, hardening checklist, backup/restore, update procedure).
- Preconditions before any remote action: local production pass (M14 backup/restore tested, dashboard authenticated), owner-authorized access method (SSH key on the host, never pasted in chat), and per-step owner authorization for first deploy.
- Secrets (BYOK API keys) live only on the target host under `~/.hermes`; never in Git, never in chat.
