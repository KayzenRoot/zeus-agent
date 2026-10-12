# ZEUS Source Pack

Project: **Zeus Agent** | Repository: `KayzenRoot/zeus-agent`

Purpose: Local-first, visually rebranded, auditable derivative of **NousResearch/hermes-agent**, with a browser-based agent operations center.

## Source hierarchy
1. `checkpoint.md` (verified project state; no speculative completions)
2. `decisions.md` (approved ADRs)
3. `scope.md`
4. `definition-of-done.md`
5. `architecture.md`
6. `requirements.md`
7. Other documents in this directory.

Unverified claims, proposed plans, and upstream issue reports are NOT proof that a bug is fixed. Code, checks, and evidence take precedence. No unattended deployment or production secret handling.

## Origin and license
Upstream: https://github.com/NousResearch/hermes-agent
License: MIT, copyright (c) 2025 Nous Research. Preserve the original MIT LICENSE and copyright notice after import. Zeus public branding is distinct from upstream attribution.
Initial upstream reference for import planning: `53df274b08f2bbbe82bb67bb50c7571952e95809` (observed 2026-10-12); re-check before import and pin the precise SHA used.

## Stage order
1. Import upstream into this existing repository with history preserved, retaining LICENSE.
2. Identify and modify user-facing assets and naming; keep internal identifiers until compatibility tests justify changes.
3. Run baseline, regression, security and UI tests locally.
4. Build web agent-operations features incrementally.
5. Consider VPS deployment only after local validation and explicit instruction.

Canonical docs and work order in this directory define the first safe increment.
