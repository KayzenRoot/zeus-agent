"""ZEUS-001: refuse inherited PowerShell and POSIX installer stages.

Preserve informational queries and dot-source/source contracts; deny actual
installation before any download, install profile, receipt or subprocess.
This is limited to fork-owned installer entrypoints, not external hosting.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = ROOT / "scripts" / "install.ps1"
POSIX = ROOT / "scripts" / "install.sh"


class ZeusInstallerStageSafetyTests(unittest.TestCase):
    def test_powershell_stages_refuse_before_initialization(self):
        code = POWERSHELL.read_text(encoding="utf-8")
        dot_source = code.index("if ($script:IsDotSourced) {")
        gate = code.index("if (-not ($ProtocolVersion -or $Manifest -or $ShowResolvedPaths))")
        denied = code.index('zeus-release-unapproved:', gate)
        initialization = code.index("\nInitialize-ResolvedPaths\n", gate)
        stage_dispatch = code.index("\nif ($Stage) {", gate)
        self.assertLess(dot_source, gate)
        self.assertLess(gate, denied)
        self.assertLess(denied, initialization)
        self.assertLess(denied, stage_dispatch)
        self.assertIn("if ($script:RunAsFile) { exit 2 }", code[gate:initialization])

    def test_posix_stages_refuse_before_runner(self):
        code = POSIX.read_text(encoding="utf-8")
        main = code.index('if [ "${BASH_SOURCE[0]:-$0}" = "$0" ]; then')
        manifest = code.index("if [ \"$WANT_MANIFEST\" = true ]; then", main)
        denial = code.index("zeus-release-unapproved:", manifest)
        runner = code.index('    check_platform\n', denial)
        self.assertLess(main, manifest)
        self.assertLess(manifest, denial)
        self.assertLess(denial, runner)
        self.assertIn("exit 2", code[denial:runner])

    @unittest.skipUnless(sys.platform == "win32", "requires native Windows PowerShell")
    def test_powershell_stage_refuses_without_creating_profile(self):
        with tempfile.TemporaryDirectory(prefix="zeus-ps-install-") as directory:
            sandbox = Path(directory)
            home = sandbox / "hermes-profile"
            install = sandbox / "install-root"
            env = os.environ.copy()
            env["HERMES_HOME"] = str(home)
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-File", str(POWERSHELL), "-Stage", "repository",
                 "-HermesHome", str(home), "-InstallDir", str(install)],
                cwd=str(sandbox), env=env,
                capture_output=True, text=True, timeout=30, check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("zeus-release-unapproved", result.stdout + result.stderr)
            self.assertFalse(home.exists())
            self.assertFalse(install.exists())
            self.assertEqual(list(sandbox.iterdir()), [])

    @unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "requires POSIX bash")
    def test_posix_stage_refuses_without_creating_profile(self):
        with tempfile.TemporaryDirectory(prefix="zeus-sh-install-") as directory:
            sandbox = Path(directory)
            home = sandbox / "hermes-profile"
            install = sandbox / "install-root"
            env = os.environ.copy()
            env["HOME"] = str(sandbox)
            env["HERMES_HOME"] = str(home)
            env["HERMES_INSTALL_DIR"] = str(install)
            result = subprocess.run(
                ["bash", str(POSIX), "--stage", "repository", "--dir", str(install)],
                cwd=str(sandbox), env=env,
                capture_output=True, text=True, timeout=10, check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("zeus-release-unapproved", result.stderr)
            self.assertFalse(home.exists())
            self.assertFalse(install.exists())
            self.assertEqual(list(sandbox.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
