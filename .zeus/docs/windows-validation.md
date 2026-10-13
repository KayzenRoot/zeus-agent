# ZEUS-001 | Windows/WSL2 validation matrix

Status: **NOT EXECUTED**. This is a reproducible runbook, not evidence that the
desktop has been installed or that a model/gateway has been exercised.

## Preconditions

- Start from the reviewed PR head; capture `git rev-parse HEAD` and the exact Windows
  build, architecture, WSL2 distro, Python and Node versions.
- Use **Node 24**, the committed lockfile, an isolated test profile, no real personal
  credentials, and loopback-only connections. Never upload secrets, user state,
  model prompts or logs to this public repository.
- Zeus release feed, signature, MSIX Publisher and rollback are **not approved**.
  Do **not** sideload, publish or install an unsigned MSIX. Do **not** run the
  upstream Hermes installer or updater against the Zeus checkout.
- Mac DMG still carries inherited binary graphics. Packaging output is
  unapproved for distribution until assets and native installation are inspected.

## Stage 1 | Static and UI checks (Windows PowerShell)

```powershell
git clone --branch work/ZEUS-001-import-brand https://github.com/KayzenRoot/zeus-agent.git
cd zeus-agent
git rev-parse HEAD
node --version
npm --version
npm ci
node --test .zeus/tests/test_desktop_release_policy.cjs
npm run --workspace web check
npm run --workspace web build
npm run --workspace apps/desktop check:lint
npm run --workspace apps/desktop test:ui
```

Record commands, exit codes, OS versions and sanitized evidence. Passing only
this stage is **not** enough to approve ZEUS-001.

## Stage 2 | Native desktop safety preflight (Windows, no unsigned MSIX)

**STOP: do not automatically run `test:desktop:fresh` on a personal Windows
profile.** Source inspection of `apps/desktop/scripts/test-desktop.mjs` found
that its `fresh` mode builds a package, launches a detached Electron process
and may encounter the first-run bootstrap path. Although it sets an isolated
`HERMES_HOME` and Electron userData, that alone is not proof the OS environment
and all backend discovery/bootstrap paths are isolated. The Zeus fork now
denies first-run bootstrap before installer download, subprocess and log I/O,
but this refusal is not an installed-app end-to-end security assessment.

Before any native smoke, independently verify at the **same HEAD**:
- All tests in `apps/desktop/electron/bootstrap-runner.test.ts` pass. In
  particular, `runBootstrap` must return `zeus-release-unapproved` without
  making an upstream HTTP request, writing any profile/marker/log or spawning
  an installer. Tests of mocked code alone do not prove host isolation.
- The OS, the checkout, the selected executable, its digest and any install
  stamp belong to Zeus and not to an existing Hermes desktop/profile.
- The tested runtime backend root is an **explicitly isolated, reviewed
  local source checkout**. Never fall back to downloading Hermes installer
  scripts. Do not use personal tokens, existing Hermes installs or a real
  default user profile.
- The native tester has a controlled shutdown and rollback procedure, with
  process ownership and paths verified before cleanup. Do not use unsigned
  MSIX, OS-level sideloading or a real upstream update feed.

Until these preconditions have objective evidence, record Stage 2 as
**BLOCKED / NOT RUN**, rather than trying the previous `fresh` command.
The `test:desktop:lifecycle` harness is also **not** automatically authorized:
its backend root, fallback behavior, process scope and cleanup must be audited
on the intended host first. The original installer protocol queries
(`--manifest`, `-Manifest`) remain informational only.

Once reviewed, conduct a supervised, isolated native source-dev run with an
explicit backend root, capture exit codes and redacted logs, and validate
launch, shutdown and profile integrity. Native smoke is separate from the
Windows JS test matrix and any future signed MSIX release gate.

## Stage 3 | Backend + dashboard WSL2

Create a *separate* ephemeral WSL2 profile following the pinned upstream
environment instructions (`AGENTS.md` and `CONTRIBUTING.md`). Verify the
backend/CLI can start, reach a test model, establish an authenticated gateway,
stream a real chat response and render the dashboard. Confirm the PTY/TUI
bridge works. Test invalid/absent auth tokens, dropped gateway connections,
reconnect and stop/restart behavior. Never bind the UI publicly for this test.

## Stage 4 | Security + identity

- UI: Zeus name, icon, settings, window/taskbar, favicon, error strings and
  localizations. Preserve legal attribution and internal compatibility keys.
- Runtime: call the desktop's existing update-check, update-apply and channel
  selection controls. Each must **refuse** with `zeus-release-unapproved`,
  without network fetch, handoff, restart or source checkout modification.
- Registry: validate `zeus://` and `zeus-dev://` on a supported
  **isolated development install only**; ensure Zeus never registers itself as
  the owner of the `hermes://` OS scheme. Do not use any unsigned MSIX.
- Security: no unauthenticated dashboard session, leaked URL token, exposed
  websocket, secret in console/logs or accidentally reachable public port.
- Native release gates: do not approve Windows MSIX until certificate subject,
  native manifest, Windows installation and uninstall, publisher, rollback and
  digest/signature verification are proven. Likewise macOS notarization,
  DMG visuals and update feed need native evidence.

## Evidence bundle template

| Field | Evidence required | Current status |
|---|---|---|
| Base/head SHA | Exact Git ref and test checkout | PENDING |
| Windows/WSL2 environment | OS, distro, Node/Python, architecture | PENDING |
| Node checks + desktop UI | Exit codes and CI/local logs | CI may provide partial evidence |
| Desktop packaged smoke | Local launch, window, clean profile, no regression | PENDING |
| Gateway/model/PT Y | One real local chat + PTY trace (redacted) | PENDING |
| Update policy | Rejected check/apply, no fetch/mutation | UNIT TEST only; runtime PENDING |
| Deep link | Windows OS activation without Hermes collision | PENDING |
| Distribution | Valid signed MSIX, publisher, fallback and rollback | BLOCKED |
| Mac | Visual DMG and notarized native validation | BLOCKED |
| Decision | Independent audit, outstanding risks, next action | CORRECTION REQUIRED |

Do not promote the PR to APPROVED until acceptance criteria and Definition of
Done have objective evidence. No merge, force-push, release or VPS deployment
under ZEUS-001 without the missing gates.
