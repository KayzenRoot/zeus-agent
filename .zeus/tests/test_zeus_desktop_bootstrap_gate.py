"""ZEUS-001: static admission-order regression checks for desktop bootstrap.

The tests intentionally do not launch Electron, Hermes Setup or the updater.
They complement the JavaScript no-I/O tests in bootstrap-runner.test.ts; they
do not prove OS-owned update registrations or native install safety.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
DESKTOP = ROOT / "apps" / "desktop" / "electron"


class ZeusDesktopBootstrapAdmissionTests(unittest.TestCase):
    def test_main_blocks_windows_recovery_before_updater_discovery_and_spawn(self):
        code = (DESKTOP / "main.ts").read_text(encoding="utf-8")
        start = code.index("async function handOffWindowsBootstrapRecovery(reason)")
        section = code[start:code.index("\n// The running app's .app bundle", start)]
        guard = section.index("if (!isZeusDesktopBootstrapApproved() || !ZEUS_NATIVE_UPDATES_APPROVED)")
        denied = section.index("return false", guard)
        discover = section.index("resolveUpdaterBinary()")
        conflict = section.index("updateHandoffConflict(HERMES_HOME)")
        spawn = section.index("spawnUpdaterProcess(")
        self.assertLess(guard, denied)
        for call in (discover, conflict, spawn):
            self.assertLess(denied, call)
        self.assertIn("ZEUS_NATIVE_UPDATES_APPROVED = false",
                      (DESKTOP / "zeus-update-policy.ts").read_text(encoding="utf-8"))

    def test_bootstrap_runner_blocks_before_logs_download_and_stage_dispatch(self):
        code = (DESKTOP / "bootstrap-runner.ts").read_text(encoding="utf-8")
        entry = code.index("async function runBootstrap(opts)")
        section = code[entry:code.index("\nexport {", entry)]
        guard = section.index("if (!isZeusDesktopBootstrapApproved())")
        deny = section.index("return { ok: false, error }", guard)
        log = section.index("openRunLog(")
        install = section.index("resolveInstallScript(", log)
        self.assertLess(guard, deny)
        self.assertLess(deny, log)
        self.assertLess(deny, install)
        self.assertIn(
            "ZEUS_DESKTOP_BOOTSTRAP_APPROVED = false",
            (DESKTOP / "zeus-bootstrap-policy.ts").read_text(encoding="utf-8"),
        )

    def test_repair_and_first_run_ipc_refuse_before_mutating_runtime(self):
        code = (DESKTOP / "main.ts").read_text(encoding="utf-8")
        repair = code[code.index("ipcMain.handle('hermes:bootstrap:repair'"):]
        guard = repair.index("if (!isZeusDesktopBootstrapApproved())")
        denial = repair.index("return { ok: false, error: ZEUS_DESKTOP_BOOTSTRAP_DENIAL }", guard)
        attempts = repair.index("bootstrapRepairAttempt += 1")
        teardown = repair.index("await teardownPrimaryBackendAndWait()")
        self.assertLess(guard, denial)
        self.assertLess(denial, attempts)
        self.assertLess(denial, teardown)
        local = code[code.index("ipcMain.handle('hermes:bootstrap:continue-local'"):]
        local_guard = local.index("if (!isZeusDesktopBootstrapApproved())")
        local_denial = local.index("return { ok: false, error: ZEUS_DESKTOP_BOOTSTRAP_DENIAL }")
        local_continue = local.index("continueFirstRunLocalBootstrap()")
        self.assertLess(local_guard, local_denial)
        self.assertLess(local_denial, local_continue)

    def test_default_installer_downloader_cannot_fetch_upstream_script(self):
        code = (DESKTOP / "bootstrap-runner.ts").read_text(encoding="utf-8")
        start = code.index("function downloadInstallScript(")
        stop = code.index("\nasync function resolveInstallScript(", start)
        downloader = code[start:stop]
        self.assertIn("Promise.reject(new Error(ZEUS_DESKTOP_BOOTSTRAP_DENIAL))", downloader)
        self.assertNotIn("https.get(", downloader)
        self.assertNotIn("createWriteStream(", downloader)
        self.assertNotIn("raw.githubusercontent.com/NousResearch/hermes-agent/", downloader)


if __name__ == "__main__":
    unittest.main()
