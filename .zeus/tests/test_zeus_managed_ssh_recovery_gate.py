"""ZEUS-001: block inherited managed-SSH update crash recovery at startup.

Main-process Electron is host-specific; this structural regression proves the
authorization gate precedes journal I/O, state claims and remote SSH dials.
It does NOT claim to exercise Windows/WSL2 or an actual SSH connection.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "apps" / "desktop" / "electron" / "main.ts"
POLICY = ROOT / "apps" / "desktop" / "electron" / "zeus-update-policy.ts"


class ZeusManagedSshRecoveryGateTests(unittest.TestCase):
    def test_release_admission_is_still_source_controlled_and_closed(self):
        policy = POLICY.read_text(encoding="utf-8")
        self.assertIn("export const ZEUS_NATIVE_UPDATES_APPROVED = false", policy)

    def test_startup_recovery_refuses_before_reading_a_journal(self):
        code = MAIN.read_text(encoding="utf-8")
        entry = code.index("async function resumeManagedSshRecoveries()")
        end = code.index("\n// Stop every pooled backend", entry)
        section = code[entry:end]
        guard = section.index("if (!ZEUS_NATIVE_UPDATES_APPROVED) {")
        denied = section.index("\n    return\n", guard)
        journal = section.index("readManagedSshRecoveryRecords()")
        launch = section.index("recoverManagedSshUpdate(record)")
        self.assertLess(guard, denied)
        self.assertLess(denied, journal)
        self.assertLess(denied, launch)
        # The call site is retained; only its operation is denied.
        self.assertIn("void resumeManagedSshRecoveries()", code)

    def test_direct_recovery_refuses_before_claim_or_ssh_transport(self):
        code = MAIN.read_text(encoding="utf-8")
        entry = code.index("async function recoverManagedSshUpdate(record)")
        end = code.index("\nasync function resumeManagedSshRecoveries()", entry)
        section = code[entry:end]
        guard = section.index("if (!ZEUS_NATIVE_UPDATES_APPROVED) {")
        denied = section.index("\n    return\n", guard)
        connection = section.index("const connectionId = record.connectionId")
        claim = section.index("managedConnectionUpdateGate.claim(")
        ssh = section.index("openManagedSshUpdateTransport(")
        recovery = section.index("recoverManagedSshScopes<any>(")
        self.assertLess(denied, connection)
        self.assertLess(denied, claim)
        self.assertLess(denied, ssh)
        self.assertLess(denied, recovery)

    def test_user_requested_update_ipc_still_has_early_denial(self):
        code = MAIN.read_text(encoding="utf-8")
        entry = code.index("async function requestManagedSshUpdate(rawId)")
        end = code.index("\nipcMain.handle('hermes:connections:update-managed'", entry)
        section = code[entry:end]
        guard = section.index("if (!ZEUS_NATIVE_UPDATES_APPROVED)")
        denial = section.index("return refusedManagedSshUpdate(", guard)
        registry = section.index("readDesktopConnectionsRegistry()")
        self.assertLess(denial, registry)
        group = code[code.index("ipcMain.handle('hermes:connections:update-all'"): ]
        group_guard = group.index("if (!ZEUS_NATIVE_UPDATES_APPROVED)")
        group_registry = group.index("readDesktopConnectionsRegistry()")
        self.assertLess(group_guard, group_registry)


if __name__ == "__main__":
    unittest.main()
