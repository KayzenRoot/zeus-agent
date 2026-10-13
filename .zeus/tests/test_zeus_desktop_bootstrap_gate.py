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
        guard = section.index("if (!ZEUS_NATIVE_UPDATES_APPROVED)")
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
        guard = section.index("if (!zeusBootstrapReleaseApproved())")
        deny = section.index("return { ok: false, error }", guard)
        log = section.index("openRunLog(")
        install = section.index("resolveInstallScript(", log)
        self.assertLess(guard, deny)
        self.assertLess(deny, log)
        self.assertLess(deny, install)
        self.assertIn("function zeusBootstrapReleaseApproved(): boolean {\n  return false", code)

    def test_default_installer_downloader_cannot_fetch_upstream_script(self):
        code = (DESKTOP / "bootstrap-runner.ts").read_text(encoding="utf-8")
        start = code.index("function downloadInstallScript(")
        stop = code.index("\nasync function resolveInstallScript(", start)
        downloader = code[start:stop]
        self.assertIn("Promise.reject(new Error('zeus-release-unapproved'))", downloader)
        self.assertNotIn("https.get(", downloader)
        self.assertNotIn("createWriteStream(", downloader)
        self.assertNotIn("raw.githubusercontent.com/NousResearch/hermes-agent/", downloader)


if __name__ == "__main__":
    unittest.main()
