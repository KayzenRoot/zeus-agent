"""ZEUS-001: inherited CMD installer must refuse without running upstream code.

Static protection is checked on all CI hosts. The process-level check runs
only on native Windows and proves the wrapper returns an error without
creating a Zeus/Hermes profile in its isolated test directory.
It is NOT evidence that PowerShell/bash installers or signed MSIX are safe.
"""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts" / "install.cmd"


class ZeusCmdInstallerGateTests(unittest.TestCase):
    def test_cmd_entrypoint_contains_only_fail_closed_commands(self):
        source = INSTALLER.read_text(encoding="utf-8")
        lines = [line.strip() for line in source.splitlines() if line.strip()]
        allowed_prefixes = ("@echo off", "setlocal", "rem ", "1>&2 echo ", "exit /b 2")
        for line in lines:
            with self.subTest(line=line):
                self.assertTrue(
                    line.lower().startswith(allowed_prefixes),
                    "CMD installer contains an unexpected executable statement",
                )
        self.assertIn("zeus-release-unapproved", source)
        self.assertEqual(lines[-1].lower(), "exit /b 2")
        self.assertFalse(
            re.search(r"(?i)(?:iex\s*\(|invoke-expression|downloadstring|invoke-webrequest)", source),
            "CMD installer still contains a remote-code execution expression",
        )

    @unittest.skipUnless(sys.platform == "win32", "native CMD execution requires Windows")
    def test_cmd_refuses_without_creating_local_install_state(self):
        with tempfile.TemporaryDirectory(prefix="zeus-cmd-gate-") as directory:
            sandbox = Path(directory)
            home = sandbox / "hermes-profile"
            install = sandbox / "zeus-install"
            env = os.environ.copy()
            env["HERMES_HOME"] = str(home)
            env["HERMES_INSTALL_DIR"] = str(install)
            result = subprocess.run(
                ["cmd.exe", "/d", "/c", str(INSTALLER)],
                cwd=str(sandbox),
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("zeus-release-unapproved", result.stdout + result.stderr)
            self.assertFalse(home.exists(), "refused wrapper created a Hermes profile")
            self.assertFalse(install.exists(), "refused wrapper created an install root")
            self.assertEqual(list(sandbox.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
