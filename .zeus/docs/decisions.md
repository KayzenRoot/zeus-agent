# Decisions Ledger
ADR-001 [APPROVED 2026-10-12]: `KayzenRoot/zeus-agent` is existing destination; DO NOT create duplicate.
ADR-002 [APPROVED 2026-10-12]: Public repository allowed by owner. Only authorized collaborators have write access, subject to GitHub permissions.
ADR-003 [APPROVED 2026-10-12]: Local Windows/WSL2 development first. No VPS work now.
ADR-004 [APPROVED 2026-10-12]: Own Zeus branding, with MIT notice and history retained. Do not break upstream integration/internal identifiers during cosmetic phase.
ADR-005 [PROPOSED]: Use authenticated browser dashboard and existing Ink TUI/PT Y bridge as foundation for Zeus agent operations center.
ADR-006 [APPROVED 2026-11-01 by owner instruction in session]: Production target extended to the owner's existing Amazon Linux VPS AFTER local production readiness. Local Windows/WSL2 remains the development surface (ADR-003 unchanged). VPS deployment must follow `.zeus/docs/deployment-vps.md`: owner-provided host, secrets only on the host, dashboard never public without auth provider, no upstream installers, controlled updates only. No remote action without explicit owner authorization per step.
