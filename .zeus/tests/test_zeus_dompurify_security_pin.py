"""ZEUS-001: reject a known vulnerable DOMPurify security pin (GHSA-cg2g-xh64-v4q7).

The offline contract checks the npm workspace and lockfile; the hosted desktop
renderer test/build plus locked npm ci remain required to prove compatibility.
This test must not turn into a replacement for running the frontend suite.
"""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MINIMUM_SAFE = (3, 4, 17)


def load_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def parts(version):
    values = version.split(".")
    if len(values) != 3 or not all(piece.isdecimal() for piece in values):
        raise ValueError(f"Unexpected DOMPurify version: {version}")
    return tuple(int(piece) for piece in values)


class ZeusDomPurifySecurityPinTests(unittest.TestCase):
    def test_desktop_and_override_match_locked_patch(self):
        root = load_json("package.json")
        desktop = load_json("apps/desktop/package.json")
        lock = load_json("package-lock.json")
        override = root["overrides"]["dompurify"]
        direct = desktop["dependencies"]["dompurify"]
        workspace = lock["packages"]["apps/desktop"]["dependencies"]["dompurify"]
        installed = lock["packages"]["node_modules/dompurify"]["version"]

        self.assertEqual({override, direct, workspace, installed}, {override})
        self.assertGreaterEqual(parts(override), MINIMUM_SAFE)

    def test_pinned_tarball_has_integrity_and_expected_registry(self):
        pkg = load_json("package-lock.json")["packages"]["node_modules/dompurify"]
        self.assertTrue(pkg["integrity"].startswith("sha512-"))
        self.assertEqual(
            pkg["resolved"],
            f"https://registry.npmjs.org/dompurify/-/dompurify-{pkg['version']}.tgz",
        )


if __name__ == "__main__":
    unittest.main()
