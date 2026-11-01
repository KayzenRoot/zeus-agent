# ZEUS-001 | Evidence delta: CI, Windows flakes, updater and DMG

Date: 2026-10-13. Review status: **CORRECTION REQUIRED / NO-GO merge / NO-GO release**.
Snapshot audited: `1766684270e4c96dfa47fd7190cedf45186c80bb` on PR #1, branch `work/ZEUS-001-import-brand`; base main `23145d788a39453fcb6d81a6a53415a822b4655f`. This file is an audit of evidence available at the cited snapshot. Subsequent documentation commits require their own CI assessment.

## 1. Hosted evidence (verified via GitHub)

- [Dashboard + desktop validation run 38414479477](https://github.com/KayzenRoot/zeus-agent/actions/runs/38414479477): **SUCCESS** in both `dashboard-checks` and `desktop-static-checks`. Desktop job contains successful locked install, release-policy Node test, typecheck + lint, update-policy Electron unit test, harness syntax check, UI unit tests, branding and OS protocol static checks. Dashboard job contains `web check`, production build and static identity checks.
- [Zeus brand unit run 38414481832](https://github.com/KayzenRoot/zeus-agent/actions/runs/38414481832): **SUCCESS**, including source update checks and notices.
- `fc6a3c870ce518751c9062356c4e77edb28021c0` and `1766684270e4c96dfa47fd7190cedf45186c80bb`: corrected three one-line native updater guards to satisfy ESLint curly and moved `./zeus-update-policy` to the ordered relative import position; CI passes at the second commit. No lint rules disabled.
- The GitHub Actions runners execute Linux + Node 24. Neither success implies Windows executable, MSIX installation, macOS DMG or WSL2 gateway/model/PTY has been tested.

## 2. Windows local report (user-supplied; raw evidence bundle not attached)

The Codex Desktop report states a clean sync at `1766684270e4c96dfa47fd7190cedf45186c80bb`, local Node **26.4**, desktop `check:lint` exit 0 with **269 warnings**, release policy **5/5**, native update gate **2/2**, harness syntax passed, Python branding passed and web build passed. The `web check` locally failed on 15-second timeouts in `SessionsPage.test.tsx` (file passed alone). The full desktop `test:ui` locally failed **15 tests across 6 files** on one run and **4 tests in different files** on another. A prior desktop test completion notification claimed exit 0 but its log reportedly contained 15 failures: **treat as FAIL, not PASS**. A separate baseline reportedly also failed 3 tests without the lint fix. None of these observations establishes root cause or proves the failures are harmless. Raw anonymized logs, process exit codes, exact failed tests and timestamps are still needed before reclassification.

### Focused triage (not executed by this audit)

1. Reproduce from a clean checkout and **Node 24** (same major as CI). Record `node --version`, `npm --version`, `git rev-parse HEAD`, Windows build, CPU/RAM, current `NODE_ENV`, antivirus activity and parallel load. Use `npm ci` with the existing lockfile. Do not downgrade checks or edit test assertions to force green.
2. Run `npm run --workspace web test -- --reporter=verbose` and `npm run --workspace apps/desktop test:ui -- --reporter=verbose`, capture each exit code and failure stack. Re-run the *same exact failing test files* alone, in a smaller group and in the full suite, preferably three repetitions in each mode; also compare `--maxWorkers=1` to the default workers on the same SHA. The named failed desktop paths are **not present in the report**: collect them before inventing targets.
3. Compare timeouts, jsdom initialization, `vi.resetModules()`, shared/global mocks, async cleanup, timer leaks, file-descriptor/process counts, and resource saturation. Existing desktop UI config in `apps/desktop/vitest.config.ts` already has `testTimeout: 15_000` and `hookTimeout: 30_000`. Do not increase timeouts before diagnosing cause.
4. Tag results `PASS / FAIL / FLAKY / NOT RUN` based on reproducible logs. File-scoped success, CI Linux success and native Windows pass are different claims. No merge until the regression/flake verdict is auditable.

## 3. Update route audit: source code inspection only

- Source CLI update interception lives in `hermes_cli/zeus_update_guard.py` plus CLI call-site guards. An existing source guard protects Zeus checkout; this audit does not claim all installer/updater paths were exercised.
- `apps/desktop/electron/main.ts` currently gates `checkUpdates`, `applyUpdates` and `hermes:updates:channel:set` on `ZEUS_NATIVE_UPDATES_APPROVED=false`, returning explicit `zeus-release-unapproved` status before strategy/feed/handoff routes. IPC names `hermes:` are compatibility contracts, not OS scheme ownership.
- `apps/desktop/electron/zeus-update-policy.ts` is fail-closed. `apps/desktop/electron-builder.config.cjs` sets both root and macOS `publish: null`; `.zeus/tests/test_desktop_release_policy.cjs` checks stable/light/bundled/store and injected release-like environment, with Node test evidence in CI.
- **Residual unproven surfaces:** Windows App Installer and registration of previously installed packages; `electron-updater` channels; channel-build manifests/Windows handoff; Mac helper, notarization and installer update; update scripts and self-update paths invoked outside Electron UI. The gate does not revoke native updater registrations created by a preexisting installation. Confirm fail-closed behavior with mocked I/O calls and an isolated test host. Do not use Hermes vendor updater to update Zeus.

## 4. DMG legacy asset inventory (metadata only, not image review)

The source tree `apps/desktop/packaging/` contains exactly two files in the directory listing inspected:

| Path | Git blob SHA (not SHA-256 file digest) | Bytes | Current reference |
|---|---|---:|---|
| `apps/desktop/packaging/nous-dmg-2b.tiff` | `cfb4e54d9ebb593852673a88b44cb523d07a4011` | 1,285,534 | `dmg.background` |
| `apps/desktop/packaging/dmg-volume.icns` | `d0f205c282e0db9bd0aff1b79290b50c902e16a7` | 606,991 | `dmg.icon` |

The configuration in `apps/desktop/electron-builder.config.cjs` references both files; the DMG title is Zeus, but filename and comments preserve upstream references. **No binary image content was opened or visually evaluated and no DMG was built.** Do not rename/delete/replace by filename alone. Next gate: inspect both images, assess IP/license and visual brand, prepare Zeus-owned replacements with verified proper retina/icon sizes, and test a real macOS DMG before publication.

## 5. Decision & STOP CONDITION

**NO-GO for merge, release, signed MSIX, sideload, VPS, or declaring ZEUS-001 DONE.** Retain PR #1 in draft while local Windows/UI flakes remain unresolved and WSL2 runtime/auth/PTY, OS `zeus://` registration, publisher certificate, signed MSIX, Windows install/uninstall/rollback, macOS DMG visuals/notarization and installer-level updater attack paths have no positive evidence.

Continue directly in the same PR with isolated, reversible changes and evidence. A CI green on documentation commits is not a substitute for a Windows or macOS native gate.
