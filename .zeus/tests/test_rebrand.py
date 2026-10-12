"""Standard-library tests for the independent Zeus brand overlay."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / ".zeus/tools/rebrand.py"
spec = importlib.util.spec_from_file_location("zeus_rebrand", PATH)
zeus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zeus)


class ZeusBrandTests(unittest.TestCase):
    def test_png_signature_dimensions_and_alpha(self):
        icon = zeus.png_icon(128)
        self.assertTrue(icon.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(struct.unpack(">II", icon[16:24]), (128, 128))
        self.assertGreater(len(icon), 100)

    def test_ico_header_and_embedded_png(self):
        icon = zeus.ico_icon()
        self.assertEqual(struct.unpack("<HHH", icon[:6]), (0, 1, 1))
        self.assertEqual(struct.unpack("<I", icon[14:18])[0], len(icon) - 22)
        self.assertEqual(icon[22:30], b"\x89PNG\r\n\x1a\n")

    def test_svg_assets_are_valid_xml(self):
        for name in ("zeus-mark.svg", "zeus-wordmark.svg"):
            document = ElementTree.parse(ROOT / ".zeus/brand" / name)
            self.assertEqual(document.getroot().tag, "{http://www.w3.org/2000/svg}svg")

    def test_replacements_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / "web/index.html"
            target.parent.mkdir()
            target.write_text("<title>Hermes Agent - Dashboard</title>", encoding="utf-8")
            pairs = zeus.REPLACEMENTS["web/index.html"][:1]
            self.assertTrue(zeus.update_text_file(root, "web/index.html", pairs))
            self.assertFalse(zeus.update_text_file(root, "web/index.html", pairs))
            self.assertEqual(target.read_text(encoding="utf-8"), "<title>Zeus Agent - Dashboard</title>")

    def test_unknown_upstream_layout_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "unknown").write_text("unrelated", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "anchor"):
                zeus.update_text_file(root, "unknown", (("Hermes", "Zeus"),))


if __name__ == "__main__":
    unittest.main()
