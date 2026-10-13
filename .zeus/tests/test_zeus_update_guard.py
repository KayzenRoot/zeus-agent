"""ZEUS-001 update safety tests, no third-party imports or network calls."""
import tempfile
import unittest
from pathlib import Path

from hermes_cli.zeus_update_guard import is_zeus_checkout, refuse_zeus_unverified_update


class ZeusUpdateGuardTest(unittest.TestCase):
    def test_canonical_zeus_checkout_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in (root / ".zeus/brand/zeus-mark.svg",
                         root / ".zeus/docs/work-orders/ZEUS-001.md"):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Zeus", encoding="utf-8")
            self.assertTrue(is_zeus_checkout(root))
            with self.assertRaises(SystemExit) as raised:
                refuse_zeus_unverified_update(root)
            self.assertEqual(raised.exception.code, 2)

    def test_only_one_marker_does_not_impact_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / ".zeus/brand/zeus-mark.svg"
            path.parent.mkdir(parents=True)
            path.write_text("Zeus", encoding="utf-8")
            self.assertFalse(is_zeus_checkout(root))
            self.assertIsNone(refuse_zeus_unverified_update(root))

    def test_emergency_recovery_is_independent_of_zeus_guard_import(self):
        """The early recovery closure must work if other modules are torn."""
        from unittest.mock import patch
        import builtins
        from hermes_cli._early_recovery import restore_interrupted_pull

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in (root / ".zeus/brand/zeus-mark.svg",
                         root / ".zeus/docs/work-orders/ZEUS-001.md"):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Zeus", encoding="utf-8")
            marker = root / ".git" / "hermes-update-pull"
            marker.parent.mkdir()
            marker.write_text("legacy", encoding="utf-8")

            original_import = builtins.__import__

            def fail_if_guard_imported(name, *args, **kwargs):
                if name == "hermes_cli.zeus_update_guard" or name == "zeus_update_guard":
                    raise AssertionError("emergency startup imported fork guard")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=fail_if_guard_imported):
                with self.assertRaisesRegex(SystemExit, "legacy Hermes update recovery is blocked"):
                    restore_interrupted_pull(root)
            self.assertEqual(marker.read_text(encoding="utf-8"), "legacy")

    def test_zeus_startup_skips_hermes_recovery_without_markers(self):
        from hermes_cli._early_recovery import restore_interrupted_pull

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in (root / ".zeus/brand/zeus-mark.svg",
                         root / ".zeus/docs/work-orders/ZEUS-001.md"):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Zeus", encoding="utf-8")
            self.assertFalse(restore_interrupted_pull(root))

    def test_zeus_startup_refuses_inherited_git_recovery_without_mutation(self):
        from hermes_cli._early_recovery import INTERRUPTED_PULL_MARKER, restore_interrupted_pull

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in (root / ".zeus/brand/zeus-mark.svg",
                         root / ".zeus/docs/work-orders/ZEUS-001.md"):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Zeus", encoding="utf-8")
            marker = root / ".git" / INTERRUPTED_PULL_MARKER
            marker.parent.mkdir(parents=True)
            marker.write_text("legacy recovery marker - do not mutate", encoding="utf-8")
            unchanged = marker.read_bytes()
            with self.assertRaisesRegex(SystemExit, "legacy Hermes update recovery is blocked"):
                restore_interrupted_pull(root)
            self.assertEqual(marker.read_bytes(), unchanged)

    def test_zeus_startup_refuses_inherited_zip_recovery_without_mutation(self):
        from hermes_cli._early_recovery import ZIP_SWAP_JOURNAL, restore_interrupted_pull

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in (root / ".zeus/brand/zeus-mark.svg",
                         root / ".zeus/docs/work-orders/ZEUS-001.md"):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Zeus", encoding="utf-8")
            journal = root / ZIP_SWAP_JOURNAL
            journal.write_text("legacy ZIP journal - do not mutate", encoding="utf-8")
            unchanged = journal.read_bytes()
            with self.assertRaisesRegex(SystemExit, "legacy Hermes update recovery is blocked"):
                restore_interrupted_pull(root)
            self.assertEqual(journal.read_bytes(), unchanged)

    def test_upstream_checkout_is_unaffected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertFalse(is_zeus_checkout(root))
            self.assertIsNone(refuse_zeus_unverified_update(root))


if __name__ == "__main__":
    unittest.main()
