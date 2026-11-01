"""ZEUS-001: destructive legacy updater reproducer must refuse before I/O.

This regression never invokes the unguarded Hermes updater; it verifies that
the Zeus entrypoint rejects every mode without modifying the sandbox.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "desktop-update" / "repro.sh"


class ZeusLegacyUpdateReproGuardTests(unittest.TestCase):
    def test_denial_precedes_user_configured_sandbox_or_dispatch(self):
        content = SCRIPT.read_text(encoding="utf-8")
        strict = content.index("set -euo pipefail")
        denial = content.index("zeus-release-unapproved:", strict)
        exit_point = content.index("exit 2", denial)
        mode = content.index('MODE="${1:-help}"')
        removal = content.index('rm -rf "$SANDBOX"')
        self.assertLess(strict, denial)
        self.assertLess(denial, exit_point)
        self.assertLess(exit_point, mode)
        self.assertLess(exit_point, removal)

    @unittest.skipUnless(shutil.which("bash"), "Bash required for native entrypoint test")
    def test_every_mode_refuses_without_erasing_existing_sandbox(self):
        with tempfile.TemporaryDirectory(prefix="zeus-update-repro-") as root:
            base = Path(root)
            sandbox = base / "sandbox"
            sandbox.mkdir()
            sentinel = sandbox / "do-not-delete.txt"
            sentinel.write_text("Zeus must not modify me", encoding="utf-8")
            other = base / "do-not-create"
            env = os.environ.copy()
            env["HERMES_UPDATE_REPRO_HOME"] = str(sandbox)
            env["HERMES_HOME"] = str(other)
            for mode in ("fresh", "behind", "error", "shim", "shim-fail",
                         "gate", "launch", "help"):
                result = subprocess.run(
                    ["bash", str(SCRIPT), mode], env=env, cwd=str(base),
                    capture_output=True, text=True, timeout=15, check=False,
                )
                self.assertEqual(result.returncode, 2, (mode, result.stdout, result.stderr))
                self.assertIn("zeus-release-unapproved", result.stderr)
                self.assertEqual(sentinel.read_text(encoding="utf-8"), "Zeus must not modify me")
                self.assertEqual(sorted(p.name for p in sandbox.iterdir()), ["do-not-delete.txt"])
                self.assertFalse(other.exists())
            self.assertEqual(sorted(p.name for p in base.iterdir()), ["sandbox"])


if __name__ == "__main__":
    unittest.main()
