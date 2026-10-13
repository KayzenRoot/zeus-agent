# ZEUS-001 | CODEX DESKTOP | Native Windows/WSL2 Validation and Corrections

**Execution state:** READY FOR CODEX. NOT EXECUTED BY CHATGPT.
**Repository:** https://github.com/KayzenRoot/zeus-agent
**Work order:** ZEUS-001 exclusively; PR #1 https://github.com/KayzenRoot/zeus-agent/pull/1 stays DRAFT / CORRECTION REQUIRED.
**Branch:** work/ZEUS-001-import-brand
**Verified baseline HEAD:** 3b491fed1ed338e7abc3f15a468e3bf874a4da6a
**Main base:** 23145d788a39453fcb6d81a6a53415a822b4655f
**Scope decision:** ADR-003 means local Windows/WSL2 first; no VPS.

## Your role and the mission

Act as a senior Windows/Electron/WSL2 integration engineer using Codex Desktop in the user's LOCAL checkout. Complete ALL safe verification and necessary in-scope corrections in one run. Prefer targeted, resource-efficient tests because hosted CI has already passed. Make independent read-only audits in parallel only if your agent platform supports it; serialize writes and resource-intensive tests. Return redacted, auditable evidence, not guesses. You are not authorized to merge, approve a release or widen scope.

## Absolute security and workflow rules

- NO VPS, cloud deployment, production tokens, signed or unsigned public distribution, merge, force push, protected branch edits, history rewrite, release/tag, OS-wide protocol registration, global installer or updater.
- Never execute inherited Hermes/Nous installer, download-and-run script, source updater, App Installer or Windows Store update. In this fork, both `ZEUS_NATIVE_UPDATES_APPROVED` and `ZEUS_DESKTOP_BOOTSTRAP_APPROVED` are intentionally false. Do NOT change, bypass, mock in production, or enable these gates.
- Never use or edit the owner's installed Hermes profile; do not overwrite existing Windows/WSL2 user data, local workspace or real configuration. Never run `git reset --hard`, `git clean`, destructive update repro or unsigned MSIX.
- Do not assume `npm run --workspace apps/desktop test:desktop:fresh` or `test:desktop:lifecycle` is safe. Those paths may spawn packaged apps, discover an external Hermes installation or seek first-run bootstrap. Require a separate strict safety preflight BEFORE any native launch.
- No username, machine ID, IP, personal screenshot, model prompt, API key, OAuth token, session transcript or real home path in a PUBLIC GitHub commit. Store detailed private evidence in a local temporary folder; sanitize any excerpt shared in public.
- Preserve MIT attribution and Hermes history, internal IPC (`hermes:` etc.), the existing Ink/PTY bridge and web dashboard. NO broad rename, second chat UI, auth rewrite or out-of-scope refactor.
- If a task needs elevation, untrusted install, real credentials, OS-wide registration, real user data or persistent external side effects, mark that ONE item BLOCKED and keep working on independent safe checks.

## Mandatory Source Pack

Read fully, in this order:
1. `.zeus/docs/checkpoint.md`, `decisions.md`, `scope.md`, `architecture.md`, `definition-of-done.md`, `work-orders/ZEUS-001.md`, `windows-validation.md`.
2. `.zeus/docs/audits/ZEUS-001-2026-10-13-installer-failclosed.md`, `ZEUS-001-2026-10-13-desktop-bootstrap-failclosed.md`, `ZEUS-001-2026-10-13-ci-windows-update-dmg.md`.
3. Root `AGENTS.md`, `CONTRIBUTING.md`, `apps/desktop/AGENTS.md`, `web/AGENTS.md`, and nested area instructions before editing.
4. CI: `.github/workflows/zeus-dashboard-validation.yml`, `zeus-windows-bootstrap-safety.yml`, `zeus-windows-test-diagnostics.yml`, `zeus-brand-unit.yml`.
5. Runtime gates: `apps/desktop/electron/zeus-bootstrap-policy.ts`, `zeus-update-policy.ts`, `bootstrap-runner.ts`, `main.ts` guards, `apps/desktop/scripts/test-desktop.mjs`; `scripts/install.cmd`, `scripts/install.ps1`, `scripts/install.sh`, `scripts/desktop-update/repro.sh`.

## Phase 0 - Local context lock and isolated evidence

- Locate the intended repo. If missing, clone the existing Zeus PR branch into a NEW empty folder. If dirty, preserve the user's changes and create a separate isolated worktree rather than resetting. Read only: `git remote -v`, `git status --porcelain=v1`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git branch --show-current`, `git log -1 --format=fuller`. Refresh GitHub PR metadata and compare exact HEAD. The pre-handoff commit is a baseline, not permission to reset newer commits.
- Record Windows version/build, CPU architecture, Node/NPM/Python/Git versions, `wsl --status`, `wsl -l -v`, locations of runtimes and backend checkouts without posting private paths.
- Create a NEW evidence directory in a private scratch workspace or %TEMP%; place all logs/screenshots only there, never in tracked public files before sanitizing.
- Baseline hosted CI at SHA 3b491fed: dashboard, Linux desktop static/typecheck/UI, Python brand/security, Windows bootstrap denial, Windows installer denial, Node 24/26.4 voice parity, Socket all SUCCESS. Windows Node26.4 full suite 10,783/10,783 passed at older SHA ac9c9ac and must NOT be called a full Windows run at the current HEAD.
- STOP writes if wrong repo/branch, unexpected protected base, local dirty state cannot be isolated, unexpected remote HEAD change or unknown authority.

## Phase 1 - Focused native Windows test parity

- Prefer Node 24 and the committed lockfile. Audit package lifecycle scripts before `npm ci --no-audit --no-fund`, and install only inside an isolated checkout. No global dependency mutation.
- Capture exact commands, exit codes, SHA and redacted output for:
  - `python -m unittest discover -s .zeus/tests -p 'test_*.py' -v`
  - `node --test .zeus/tests/test_desktop_release_policy.cjs`
  - `npm run --workspace apps/desktop test:desktop:platforms -- electron/bootstrap-runner.test.ts`
  - `npm run --workspace apps/desktop test:desktop:platforms -- electron/zeus-update-policy.test.ts`
  - `npm run --workspace apps/desktop check:lint`
  - `npm run --workspace web check`
  - `npm run --workspace web build`
- If available without a new global install, compare targeted voice-prefs tests with Node 24 and 26.4 on the same HEAD. Run the enormous full suite only when a new local regression or functional patch justifies it; avoid wasting 27+ minutes repeating CI for no reason.
- Execute only the sandboxed *refusal tests* for installer/update paths. Require `zeus-release-unapproved` and no new directory, subprocess, network or marker. Never run actual installer against real profile.
- For failures: reproduce isolated and in suite, trace root cause, make minimal changes, add behavior regression, rerun affected checks. Never hide failures by skipped tests or arbitrary timeout increases.

## Phase 2 - Native Electron safety preflight; conditional visual smoke

BEFORE any Electron launch:
- Trace every path for install stamp, backend discovery, update handoff, bootstrap, userData, `HERMES_HOME` and process ownership. Confirm the chosen executable is built from THIS Zeus checkout, never an existing Hermes desktop. Compute digest, inspect metadata, ensure no OS-wide writes, shell profile mutation, unexpected fallback or detached orphan process.
- The thin packaged build may require first-run installation, which must currently fail closed. That is EXPECTED DENIAL, not a successful desktop bootstrap. DO NOT turn gates on to make a demonstration work.
- Do not execute `test:desktop:fresh` or `test:desktop:lifecycle` until you have provable isolation, trusted explicit backend root and a controlled cleanup plan. No unsigned MSIX or OS protocol registration.
- If a safe source-dev backend already exists in a separate scratch checkout and all prerequisites above hold, launch the dev app as a test-owned child (not detached) with ephemeral `HERMES_HOME`, Electron userData, workspace and loopback-only endpoints. Inspect brand/icon/title, window, lifecycle and shutdown. Capture sanitized screenshots and check that no real Hermes instance/user profile was contacted. Terminate ONLY owned PIDs, never kill by process name.
- If native launch cannot satisfy all requirements, label it BLOCKED with exact prerequisite and continue other checks; do not attempt an unauthorized bootstrap.

## Phase 3 - WSL2 runtime/backend/dashboard, conditionally

- Read PM-specific instructions and WSL2 environment. Do NOT run `wsl --install`, change system features, use real Hermes HOME, or execute remote install scripts.
- If WSL2 and a reviewed local runtime are already safely available, set an isolated ephemeral profile and run project-supported development commands only after confirming that dependency bootstrap cannot touch the user's real profile or invoke Hermes updater. Otherwise record BLOCKED and continue.
- Bind all test endpoints to 127.0.0.1. Verify backend health, dashboard authentication (valid test credential and unauthorized denial), gateway connection, streaming test chat using an already authorized test model, TUI/PTY, disconnect/reconnect, shutdown/restart and owned process cleanup.
- Do not request personal API keys or store prompts/tokens in a public artifact. If model is unavailable, record model/chat BLOCKED individually, not fabricated PASS.

## Phase 4 - Non-destructive native identity/security audit

- Review protocol `zeus://` and `zeus-dev://` handling, guarantee there is no unintended OS ownership of `hermes://`. Read declarations, but do NOT register protocols system-wide without supervised approved isolated development install.
- Audit Publisher and signed MSIX readiness, digest/signature, packaging variants, `publish:null`, old OS App Installer/Store registrations (read-only only), Windows updater helper guards, source CLI updater, remote managed SSH update gate, DMG background/ICNS/attribution and rollback design.
- Keep clear separate findings for FAIL-CLOSED Zeus code and updater behavior that Microsoft Windows might manage outside Zeus's process. Unit tests are NOT proof that previously installed OS registrations are revoked.
- Do not create/launch unsigned MSIX, sign with a fake identity, notarize/distribute DMG, enable feeds or make claims unsupported by native evidence.

## Phase 5 - Minimal corrections and CI

- Classify each result exactly PASS, FAIL, BLOCKED, NOT RUN or EXPECTED DENIAL. For a confirmed in-scope bug: propose fix, add focused regression, implement on ZEUS-001's EXISTING branch, run targeted tests, commit and push with a normal fast-forward only if safe. Never force push, merge, create unrelated PR or broaden the work order.
- If remote branch changes, fetch and reconcile; stop unsafe writes. Check CI SHA after every functional fix. Keep code/architecture/internal compatibility stable. No mass cleanup, automatic merges or state promotion.
- Update a NEW timestamped sanitized audit/checkpoint delta; do not overwrite history or claim the canonical checkpoint APPROVED without all gates. Keep issues #2/#3/#4/#5 open until their true DoD is met.

## Phase 6 - Evidence Bundle required

Write PRIVATE LOCAL files (not public tracked secrets) and package as `ZEUS-001-CODEX-LOCAL-EVIDENCE.zip`:
- `manifest.json`: repo, branch/base/initial/final HEAD, Windows/WSL2 versions, sanitization status, commands + exit codes, actual CI URLs, per-gate outcomes.
- `diagnostic.md`: confirmed findings with exact source paths/line ranges, causes and before/after.
- `test-results.md`: commands, exit statuses and logs with no secrets; explain why any expensive test was skipped.
- `checkpoint-delta.md`: evidence-backed verified facts vs. outstanding prerequisites and honest verdict.
- Screenshots/log excerpts ONLY if sanitized and local, with SHA256 checksums for each included file.
- Link commits/PR and CI without exposing local/private data. No uploading this zip to the public repo automatically.

## Exit rule and report to owner

Progress through **all independent safe work** in this execution, even if a specific stage blocks. A BLOCKED local native test is NOT authorization to disable update protections.

Return in Portuguese:
1. Exact repo, branch, main base, starting/final SHA and PR state.
2. PASS/FAIL/BLOCKED/NOT RUN table for every stage, with objective evidence.
3. Which native Windows/WSL2 operations actually ran; which were only audited.
4. In-scope fixes and any new tests, with CI links; risks and open issues.
5. LOCAL absolute path to evidence ZIP and next concrete step for ChatGPT review.
6. Decision: `CORRECTION REQUIRED` until true local integration, signing and review gates are fulfilled.

**STOP: no merge, release, OS-level unsigned install, update bypass or VPS.**
