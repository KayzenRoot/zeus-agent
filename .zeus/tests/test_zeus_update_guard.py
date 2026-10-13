"""ZEUS-001 update safety tests, no third-party imports or network calls."""
import tempfile
import unittest
from pathlib import Path

from hermes_cli.zeus_update_guard import is_zeus_checkout, refuse_zeus_unverified_update


class ZeusUpdateGuardTest(unittest.TestCase):
    def test_dashboard_api_refuses_before_launching_upstream_updater(self):
        """Structural gate: the dashboard route must deny before action receipts or I/O."""
        import ast

        route = Path(__file__).resolve().parents[2] / "hermes_cli/web_routers/actions.py"
        tree = ast.parse(route.read_text(encoding="utf-8"))
        handler = next(
            node for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "update_hermes"
        )
        # First executable statement after docstring imports the guard.
        first, second = handler.body[1:3]
        self.assertIsInstance(first, ast.ImportFrom)
        self.assertEqual(first.module, "hermes_cli.zeus_update_guard")
        self.assertEqual([name.name for name in first.names], ["is_zeus_checkout"])
        self.assertIsInstance(second, ast.If)
        self.assertIn("is_zeus_checkout", ast.unparse(second.test))
        self.assertIn("PROJECT_ROOT", ast.unparse(second.test))
        self.assertIsInstance(second.body[0], ast.Return)
        rejected = ast.unparse(second.body[0].value)
        self.assertIn("zeus-release-unapproved", rejected)
        self.assertIn("'ok': False", rejected)
        self.assertNotIn("_update_refused", rejected)

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

    def test_partial_or_missing_markers_do_not_enable_upstream_updates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for marker in (None, ".zeus/brand/zeus-mark.svg"):
                if marker:
                    path = root / marker
                    path.parent.mkdir(parents=True)
                    path.write_text("Zeus", encoding="utf-8")
                self.assertTrue(is_zeus_checkout(root))
                with self.assertRaises(SystemExit) as raised:
                    refuse_zeus_unverified_update(root)
                self.assertEqual(raised.exception.code, 2)

    def test_packaged_layout_without_source_docs_is_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary) / "agent-payload" / "hermes-agent"
            payload.mkdir(parents=True)
            self.assertFalse((payload / ".zeus").exists())
            self.assertTrue(is_zeus_checkout(payload))
            with self.assertRaises(SystemExit) as raised:
                refuse_zeus_unverified_update(payload)
            self.assertEqual(raised.exception.code, 2)

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

    def test_packaged_runtime_without_source_markers_refuses_legacy_recovery(self):
        from hermes_cli._early_recovery import INTERRUPTED_PULL_MARKER, restore_interrupted_pull

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "agent-payload" / "hermes-agent"
            marker = root / ".git" / INTERRUPTED_PULL_MARKER
            marker.parent.mkdir(parents=True)
            marker.write_text("legacy leftover", encoding="utf-8")
            self.assertFalse((root / ".zeus").exists())
            with self.assertRaisesRegex(SystemExit, "legacy Hermes update recovery is blocked"):
                restore_interrupted_pull(root)
            self.assertEqual(marker.read_text(encoding="utf-8"), "legacy leftover")

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

    def test_arbitrary_root_does_not_weaken_this_fork_guard(self):
        # Real upstream Hermes does not ship this fork-specific code.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertTrue(is_zeus_checkout(root))
            with self.assertRaises(SystemExit) as raised:
                refuse_zeus_unverified_update(root)
            self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
