"""ZEUS-001 direct desktop-update shell entrypoint admission.

Run without launching any Hermes update, powershell, GUI, network or real
installation. The POSIX test executes bash in an ephemeral empty directory.
Windows source-order checks are static, not Windows host validation.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class HandoffSourceGateTests(unittest.TestCase):
    def test_windows_handoff_denies_before_upstream_bootstrap_and_marker(self):
        code = (ROOT / "scripts/desktop-update/windows.ps1").read_text(encoding="utf-8")
        # PowerShell's top-level param() must stay before any code.
        header = code.index("    [int]$CustodyOf = 0\n)\n")
        guard = code.index("[Console]::Error.WriteLine(\"zeus-release-unapproved", header)
        stopped = code.index("exit 2", guard)
        first_marker = code.index("if ($MarkerOp -and -not $InstallRoot)")
        first_disk_write = code.index("New-Item -ItemType Directory -Path $LogDir")
        self.assertLess(header, guard)
        self.assertLess(guard, stopped)
        self.assertLess(stopped, first_marker)
        self.assertLess(stopped, first_disk_write)
        self.assertLess(stopped, code.index("Invoke-MarkerClaim"))

    def test_compatibility_forwarder_denies_before_target_resolution(self):
        code = (ROOT / "scripts/desktop-update.ps1").read_text(encoding="utf-8")
        guard = code.index("[Console]::Error.WriteLine(\"zeus-release-unapproved")
        stopped = code.index("exit 2", guard)
        self.assertLess(stopped, code.index('$target = Join-Path'))

    def test_posix_script_refuses_before_state_or_subprocess_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            home = sandbox / "profile"
            root = sandbox / "untrusted-install"
            script = ROOT / "scripts/desktop-update/posix.sh"
            env = os.environ.copy()
            env["HERMES_HOME"] = str(home)
            env["ZEUS_NATIVE_UPDATES_APPROVED"] = "true"  # ignored user-controlled value
            result = subprocess.run(
                ["bash", str(script), "--install-root", str(root), "--no-ui"],
                cwd=str(sandbox), env=env,
                capture_output=True, text=True, timeout=10, check=False,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("zeus-release-unapproved", result.stderr)
            self.assertFalse(home.exists(), "handoff created the profile before denying")
            self.assertFalse(root.exists(), "handoff mutated the install before denying")
            self.assertEqual(list(sandbox.iterdir()), [])

    def test_posix_source_gate_precedes_original_arguments(self):
        code = (ROOT / "scripts/desktop-update/posix.sh").read_text(encoding="utf-8")
        guard = code.index("printf '%s\\n' 'zeus-release-unapproved")
        stopped = code.index("exit 2", guard)
        self.assertLess(guard, stopped)
        self.assertLess(stopped, code.index('ORIGINAL_ARGS=("$@")'))
        self.assertLess(stopped, code.index('mkdir -p "$LOG_DIR"'))


if __name__ == "__main__":
    unittest.main()
