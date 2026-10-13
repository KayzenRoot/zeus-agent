# ZEUS-001 Checkpoint | 2026-10-12

## Authority and boundaries
- Repository: `KayzenRoot/zeus-agent` (owner-approved public). Source Pack: `.zeus/docs`. Work Order: `ZEUS-001`.
- PR: https://github.com/KayzenRoot/zeus-agent/pull/1, **draft / CORRECTION REQUIRED**, base `main` at `23145d788a39453fcb6d81a6a53415a822b4655f`.
- Branch: `work/ZEUS-001-import-brand`. No authorized merge, force-push, external publication or VPS deployment.
- Import pinned from `NousResearch/hermes-agent` commit `53df274b08f2bbbe82bb67bb50c7571952e95809`. Upstream commit ancestry preserved by the import process; upstream MIT license and copyright retained.

## VERIFIED implementation
- Upstream import GitHub Action success: https://github.com/KayzenRoot/zeus-agent/actions/runs/38312076398
- Zeus SVG marks/banner, favicon, desktop icon PNG/ICO/ICNS, Icon Composer and MSIX tiles, i18n display text, dashboard title/sidebar/footer, own README.
- CLI `zeus` alias; `hermes` internal package and protocol names intentionally preserved for compatibility.
- Desktop product IDs/executable/MSIX declaration under `com.kayzenroot.*` / `KayzenRoot.*`; these are NOT proof of installable, valid signed packages.
- Brand assets regeneration succeeded: https://github.com/KayzenRoot/zeus-agent/actions/runs/38314034954
- Desktop display test expectation correction in commit `583465c625da7aac19123a379a72d0305141b5f2`.
- **All dashboard and desktop static/UI CI jobs passed at `583465c`**: https://github.com/KayzenRoot/zeus-agent/actions/runs/38317333954
- **Zeus brand unit tests passed at `583465c`**: https://github.com/KayzenRoot/zeus-agent/actions/runs/38317334118
- Source updater guard added in commit `ebc23a5a532f4e04cdcfaed1b11bbe4cb4c6000e`: blocks `zeus update` and `hermes update` for the marked Zeus source checkout until an independently audited Zeus update channel exists. Brand unit tests passed at this commit: https://github.com/KayzenRoot/zeus-agent/actions/runs/38337939300
- **CI on `ebc23a5` was still in progress at the time of this checkpoint**; recheck https://github.com/KayzenRoot/zeus-agent/actions/runs/38337939298 before claiming green.

## BLOCKERS / CORRECTION REQUIRED
1. Windows/WSL2 local runtime not validated (backend start, model, gateway, chat, PTY, auth and UI walkthrough); keep all tests local-first; VPS strictly out of scope.
2. Windows MSIX signature and actual Publisher certificate NOT validated. `CN=KayzenRoot` is only a provisional manifest value, not proof of any signing key. Do not publish installers.
3. Desktop OS URI registration is now `zeus://` (plus `zeus-dev://` in development) in commit `42091e483aecb375c2374f5fb343f0178728c0ff`; Electron `hermes:` IPC remains intact and forwarded legacy Hermes deep links may still be parsed. **Typecheck, desktop UI tests and a real Windows deep-link activation are pending for this change.** Internal `hermes:` IPC messages must not be blindly renamed.
4. Installer DMG packaging still references Nous-era background/icons (`packaging/nous-dmg-2b.tiff`, `packaging/dmg-volume.icns`). Replace only after asset inspection and native build tests.
5. No vetted Zeus-owned release distribution/update manifest, signature verification, forward/rollback pipeline or source publisher. Source updates are temporarily blocked by the guard; further packaged updater paths require audit.
6. Python regression suite, Electron platform-specific integration tests, macOS dmg/MSIX native packaging, image visual verification and authenticated dashboard security smoke still outstanding.
7. Full downstream replacement of every historical Hermes mention is NOT the goal. Preserve MIT legal notices, code identifiers and compatibility paths. Review public-visible brand leftovers scoped to shipped surfaces.

## Resume workflow
- Read this checkpoint, decisions, scope, DoD and `work-orders/ZEUS-001.md`.
- Revalidate GitHub PR HEAD and CI; fix failing gates on this same branch.
- Audit deep links/installer resources/update policy with isolated tests; produce a local Windows/WSL2 runbook and evidence.
- Only promote ZEUS-001 to APPROVED after all DoD evidence; otherwise keep the PR draft and record the exact blocked criteria.

**STOP CONDITION: do not merge or distribute until all critical acceptance gates have factual evidence.**


## 2026-10-13 | ZEUS-001 Correction Delta (NOT APPROVED)

**Base:** `23145d788a39453fcb6d81a6a53415a822b4655f`.
**Implementation snapshot before this checkpoint:** `59c0650bb070bed5357123f3c7738cb799546b5c`.
PR remains **DRAFT / CORRECTION REQUIRED**. No merge, deploy, Windows
installation, publisher approval or VPS changes.

### Newly verified

- Earlier implementation HEAD `f3272786e9b82a7fa810e3dd8e5a0b21e5c63569`
  passed [Zeus brand tests](https://github.com/KayzenRoot/zeus-agent/actions/runs/38338428085)
  and [dashboard + desktop static/UI checks](https://github.com/KayzenRoot/zeus-agent/actions/runs/38338427952).
- Subsequent correction commits on the same PR added a fail-closed
  desktop update admission policy, refusing native update check/apply and
  channel selection before feed/network/handoff I/O
  (`apps/desktop/electron/zeus-update-policy.ts`,
  `apps/desktop/electron/main.ts`). Product packaging explicitly omits
  native updater feeds in all variants
  (`apps/desktop/electron-builder.config.cjs`).
- Added real-config Node regression cases for stable/light/bundled/store
  and release-like environment. The **specific packaging-policy step**
  succeeded in the intermediate
  [desktop CI run 38395118328](https://github.com/KayzenRoot/zeus-agent/actions/runs/38395118328).
  This is NOT a claim that the whole run succeeded.
- Updated desktop source repository metadata while retaining original
  Nous Research author and MIT attribution. Replaced DMG title and
  Linux summary strings, not uninspected DMG binary graphics.
- Updated `apps/desktop/scripts/test-desktop.mjs` to derive app/executable
  and DMG names from Zeus product identity. Added
  [Windows/WSL2 validation matrix](windows-validation.md).
  The harness has **not** been exercised on a real Windows machine.

### Explicitly unverified at this checkpoint

- Full latest HEAD dashboard/desktop CI, UI suite, typecheck and lint:
  running/pending; read the current PR head and its checks before
  declaring green. Re-runs cancelled by subsequent commits are not
  evidence of passing.
- Independent review of all native updater/OS-managed update routes,
  actual Windows MSIX Publisher certificate/signing, installation,
  `zeus://` OS handler, macOS notarized DMG, local gateway/model/PTY,
  authenticated UI and Python backend regressions.
- No native distribution channel, auto-update, release artifact or
  merge is authorized or validated. Package-level protection does not
  claim to cancel update registrations of any previously installed
  OS-managed packages.

**Next necessary gate:** finish the HEAD CI, correct failures on
the same ZEUS-001 PR, run isolated native Windows/WSL2 validation
and complete release signature/visual security evidence. Preserve
the **CORRECTION REQUIRED** verdict until independent audit confirms DoD.


## CI WINDOWS FOLLOW-UP 2026-10-13 | Verified HEAD `1766684270e4c96dfa47fd7190cedf45186c80bb`

**Current decisive evidence for implementation SHA `1766684270e4c96dfa47fd7190cedf45186c80bb` (supersedes earlier "CI pending" status above):** [run 38414479477](https://github.com/KayzenRoot/zeus-agent/actions/runs/38414479477) = **dashboard-checks SUCCESS, desktop-static-checks SUCCESS**, including desktop lint, UI tests, native update-policy tests, release-config tests and static OS protocol checks. [Zeus brand tests 38414481832](https://github.com/KayzenRoot/zeus-agent/actions/runs/38414481832) = **SUCCESS**. Fix commits: `fc6a3c870ce518751c9062356c4e77edb28021c0`, `1766684270e4c96dfa47fd7190cedf45186c80bb`; no rule disabled. Base main remains `23145d788a39453fcb6d81a6a53415a822b4655f`. PR #1 still DRAFT.

**Local Windows evidence (reported, not independently reproduced here):** Node 26.4, desktop lint exit 0 with 269 warnings, policy 5/5, update policy 2/2, web build/branding passed; `web check` timeout in SessionsPage tests, `test:ui` returned inconsistent failing sets (15 failures/6 files then 4 failures in other files). No complete local UI PASS is accepted. Linux CI and local Windows are not interchangeable. Review [audit & reproduction matrix](audits/ZEUS-001-2026-10-13-ci-windows-update-dmg.md).

**Remaining stop gates:** native Windows/WSL2 smoke with model, gateway, PTY and auth; deterministic diagnosis of test instability; MSIX real Publisher/signature/install/uninstall/rollback; updater route audit beyond UI gate, including OS-owned registrations; `zeus://` OS activation; inherited DMG TIFF/ICNS visual/legal inspection and Mac build. No independent proof of these exists. **Verdict: CORRECTION REQUIRED, NO-GO merge/release; do not deploy to VPS.** This checkpoint commit itself is a newer HEAD and must receive its own CI before claiming that newer HEAD green.


## NODE26 VOICE PREFS REPRO 2026-10-13 | Regression delta

**Last independently PASS implementation before this correction:** `f51c5582b0efd9f26eb82275e9c9538166494027` on [brand CI 38429315103](https://github.com/KayzenRoot/zeus-agent/actions/runs/38429315103) and [dashboard + desktop Linux CI 38429315149](https://github.com/KayzenRoot/zeus-agent/actions/runs/38429315149). PR #1 still DRAFT / CORRECTION REQUIRED; main unchanged at `23145d788a39453fcb6d81a6a53415a822b4655f`.

**Real failure reproduced on Windows/Node 26.4.0**: [Windows CI 38425723776](https://github.com/KayzenRoot/zeus-agent/actions/runs/38425723776) on earlier `229289d` ended **FAIL**, despite isolated SessionsPage and full web suites passing. Desktop UI: **10,781 passed / 2 failed out of 10,783**. Both failures are in `src/store/voice-prefs.test.ts` at lines 44 and 72: expected `localStorage.getItem('hermes.desktop.autoSpeakReplies')` to be `null` after mocked quota/security failure, but got `'false'`. CI log also emitted Node 26 native localStorage unavailability warnings. This confirms a test-environment spy mismatch (the Node 26 jsdom fallback has its own `setItem`, not inherited `Storage.prototype.setItem`), not an established runtime product data loss bug.

**Corrective candidate:** make the failing tests spy on `Storage.prototype` for real jsdom storage or on the actual fallback `localStorage` for the alternative object. Keep the quota/security exceptions and assertions intact, with NO blanket skip and NO relaxed timeouts. Added a targeted Windows matrix workflow for Node 24 and Node 26.4.0; **PENDING** at this documentation snapshot, must read the new commit's CI results before considering fixed. The full Windows Node 26.4 UI suite, local repro, native Windows/WSL2, signed MSIX and macOS DMG remain separate gates. No merge/release/VPS.
