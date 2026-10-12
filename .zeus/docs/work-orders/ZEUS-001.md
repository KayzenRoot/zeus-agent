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
