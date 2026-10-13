# ZEUS-001 | Managed SSH crash recovery auto-start | Security delta R4

Date: 2026-10-13. Parent source HEAD: `2167a11d6b54e3cdb57af1c56065de379bde987c`. PR #1, branch `work/ZEUS-001-import-brand`.
Status: **CORRECTION REQUIRED**. NO-GO merge, release, VPS.

## Finding

The interactive Electron paths `hermes:connections:update-managed` and `hermes:connections:update-all` already tested the source-controlled `ZEUS_NATIVE_UPDATES_APPROVED=false` before starting any update.

A separate path was reachable **on every Electron startup**: `void resumeManagedSshRecoveries()` in `apps/desktop/electron/main.ts`. It immediately read `managed-ssh-update-recovery.json`, then dispatched `recoverManagedSshUpdate(record)` for saved entries. That callback could claim update state and call `openManagedSshUpdateTransport(record.source)`, wait for remote marker clearance, and restore remote backend scopes. This path did not consult the Zeus update gate. It is a **potential remote network/process side effect when a preexisting recovery journal is present**, even if no user presses Update.

This finding is from source inspection, **not** a reproduced native network execution. Do not claim that an SSH connection was actually made.

## Correction

- At entry of `resumeManagedSshRecoveries()`, return immediately if `!ZEUS_NATIVE_UPDATES_APPROVED`, before reading the saved journal or dispatching callbacks.
- At entry of `recoverManagedSshUpdate(record)`, repeat the same gate before touching the record, claiming a connection, opening SSH transport, waiting for markers, or restarting a backend.
- Keep `managed-ssh-update-recovery.json` **untouched**: do not silently remove historical recovery evidence or pretend the remote install has been restored.
- Preserve existing IPC strings, regular SSH connection functionality, updater gate semantics and stored recovery implementation for a later, separately approved migration.

## Evidence requirements

`.zeus/tests/test_zeus_managed_ssh_recovery_gate.py` enforces gate placement, source policy and previously guarded update IPC boundaries. The brand/security Python CI includes these tests; Electron lint and UI validation must also pass on the **new HEAD**. A test of source ordering is not a substitute for native Electron/SSH behavior.

## Residual risk / hard stop

Previously registered OS-managed App Installer/Store update sources can operate outside the Electron process; signing, publisher, digest, rollback and native source-development smoke are still missing. Normal app SSH connectivity may be user-directed; this change only refuses an update-recovery side effect at startup.

Review state **CORRECTION REQUIRED** until CI of the exact correction commit is verified and the Codex Windows/WSL2 native evidence bundle is independently reviewed. No update re-enablement, merge, release, unsigned MSIX or VPS.
