"""ZEUS-001: stand-alone Windows updater helper entrypoints fail closed.

These tests run on Linux CI without importing pywinrt or requiring Windows.
They prove the public helper main() refuses before any WinRT/Store operation.
They do not prove OS-managed App Installer registrations are revoked.
"""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

from hermes_cli import windows_appinstaller_update as appinstaller
from hermes_cli import windows_store_update as store


class NativeUpdateHelperGateTest(unittest.TestCase):
    def test_appinstaller_direct_entrypoint_denies_without_winrt(self):
        stdout = io.StringIO()
        with patch.object(appinstaller, "_load_projection", side_effect=AssertionError("WinRT loaded")):
            with contextlib.redirect_stdout(stdout):
                exit_code = appinstaller.main()
        self.assertEqual(exit_code, 1)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["error"], "zeus-release-unapproved")
        self.assertIsNone(result["available"])
        self.assertFalse(result["ok"])
        self.assertNotIn("source_uri", result)

    def test_store_direct_entrypoint_refuses_check_download_and_install(self):
        for mode in ("check", "download", "install"):
            with self.subTest(mode=mode):
                stdout = io.StringIO()
                with patch.object(store.site, "addsitedir", side_effect=AssertionError(".pth executed")):
                    with patch.object(store, "_execute", side_effect=AssertionError("StoreContext used")):
                        with contextlib.redirect_stdout(stdout):
                            exit_code = store.main(["--mode", mode, "--hwnd", "7"])
                self.assertEqual(exit_code, 1)
                result = json.loads(stdout.getvalue())
                self.assertEqual(result["error"], "zeus-release-unapproved")
                self.assertFalse(result["ok"])
                self.assertIsNone(result["available"])


if __name__ == "__main__":
    unittest.main()
