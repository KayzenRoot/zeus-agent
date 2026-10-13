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
