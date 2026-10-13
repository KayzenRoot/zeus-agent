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

    def test_upstream_checkout_is_unaffected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertFalse(is_zeus_checkout(root))
            self.assertIsNone(refuse_zeus_unverified_update(root))


if __name__ == "__main__":
    unittest.main()
