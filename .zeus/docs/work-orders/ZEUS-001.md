# Work Order ZEUS-001
OBJECTIVE: deliver a locally testable Zeus-branded fork based on original Hermes history in existing repository.
CONTEXT: public repository initially empty; MIT source; owner-approved public visibility and local-only development.
SCOPE: import upstream main at recorded SHA with full Git ancestry; audited user-facing naming + SVG/icon update; minimum focused tests and evidence.
OUT OF SCOPE: VPS, auth redesign, broad internal `hermes` identifier rename, agent orchestration.
FILES/SOURCES TO READ: .zeus/docs; upstream AGENTS.md, web/AGENTS.md, LICENSE, web/src/, assets/, package.json, pyproject.toml; Git refs and lockfiles.
REQUIREMENTS: R1-R8. ARCHITECTURE RULES: preserve Ink/TUI bridge and API compatibility; no second chat UI.
CONSTRAINTS: no secrets; public repo; no destructive force-push; no unreviewed merges; changes local-first; staged file audit.
ACCEPTANCE CRITERIA: source/history and MIT notice intact; visual strings/asset tests pass; dashboard executes on local dev machine; no reported regressions; PR reviewed.
TESTS: baseline and delta targeted tests, npm checks, visual browser smoke, auth checks, secrets scan.
DELIVERABLES: code, design assets, evidence, PR, proposed checkpoint delta.
REVIEW FORMAT: Portuguese, APPROVED/CORRECTION REQUIRED/BLOCKED, with failures and concrete paths.
STOP CONDITION: stop until any high severity error corrected and work order objectively approved.


## CI WINDOWS FOLLOW-UP 2026-10-13 | Acceptance gate reconciliation

- Latest independently verified implementation snapshot: `1766684270e4c96dfa47fd7190cedf45186c80bb`, PR #1 still draft; `main` base `23145d788a39453fcb6d81a6a53415a822b4655f`. [Dashboard + desktop CI success](https://github.com/KayzenRoot/zeus-agent/actions/runs/38414479477), [brand CI success](https://github.com/KayzenRoot/zeus-agent/actions/runs/38414481832).
- Static/typecheck/lint/CI UI: **PASS in hosted Linux Node 24**; local Windows Node 26.4 UI and web tests: **FAIL/FLAKY REPORTED**, no independently collected failure logs; do not mark as passed.
- Actual Windows/WSL2 runtime, gateway/model/PTY/auth and OS deep links: **NOT RUN**. Windows MSIX signing Publisher/certificate/install/rollback: **BLOCKED**. macOS DMG legacy assets/notarization: **NOT RUN**. Full release/update routes beyond fail-closed CLI and Electron UI gates: **AUDIT INCOMPLETE**.
- **Next execution:** first capture exact failing tests/logs on Windows using Node 24 parity; compare isolated vs suite runs, worker concurrency and JS DOM cleanup without relaxing timeouts. Then isolated native Windows/WSL2 smoke (no unsigned MSIX), regression audit of OS-managed update surfaces, visual TIFF/ICNS review, and genuine publisher verification. Document outcome/exit codes in a future checkpoint.
- Tracking and precise evidence: [ZEUS-001 audit](../audits/ZEUS-001-2026-10-13-ci-windows-update-dmg.md), [Windows validation runbook](../windows-validation.md).
- **Gate decision stays CORRECTION REQUIRED / NO-GO merge and release.** No merge/force push/VPS/distribution while any native/high-risk gate lacks evidence.


## NODE26 VOICE PREFS REPRO 2026-10-13 | Acceptance delta

- Windows/Node 26.4 CI [run 38425723776](https://github.com/KayzenRoot/zeus-agent/actions/runs/38425723776) **FAILED 2/10,783 desktop UI tests** in `apps/desktop/src/store/voice-prefs.test.ts` on mocked localStorage write failure; isolated SessionsPage and full web suite passed. Node 24 Windows earlier [run 38419378102](https://github.com/KayzenRoot/zeus-agent/actions/runs/38419378102) passed 10,783/10,783 UI tests on SHA `906de67`.
- Correct the test mock target for fallback storage in Node 26 without hiding storage exceptions, and require focused Windows **Node 24 + 26.4.0** PASS on the same updated SHA; thereafter full Node 26 UI run to catch interactions.
- Linux full dashboard + desktop CI and brand CI passed at `f51c558`; the corrective commit must independently pass. Do not close #2 from a focused-only test. Native runtime/MSIX/DMG tests still pending. **NO-GO merge/release/VPS.**
