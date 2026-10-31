"""ZEUS-001: reject re-entry below the dependency security floors fixed in CD09.

Offline contract over the committed manifests and lockfiles. Compatibility of
the bumped majors (simple-git 4, oauthlib 4, filelock 4, tinypool 2) still
requires the hosted suites (dashboard/desktop static checks, windows-js-tests)
and, for runtime Python, an environment prepared through PM; this file only
stops the vulnerable pins from returning silently.
"""

import json
import re
import tomllib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def load_toml(relative_path):
    with (ROOT / relative_path).open("rb") as fp:
        return tomllib.load(fp)


def parts(version):
    """Version tuple of arbitrary depth ('1.2.1.0', '2026.10.18', ...)."""
    return tuple(int(piece) for piece in version.split(".") if piece.isdecimal())


def at_least(version, floor):
    a = parts(version) if isinstance(version, str) else tuple(version)
    b = parts(floor) if isinstance(floor, str) else tuple(floor)
    width = max(len(a), len(b))
    a += (0,) * (width - len(a))
    b += (0,) * (width - len(b))
    return a >= b


def uv_packages():
    return {pkg["name"]: pkg["version"] for pkg in load_toml("uv.lock")["package"]}


class ZeusNpmRootSecurityFloors(unittest.TestCase):
    """Root workspace lockfile — Trivy package-lock.json target."""

    def test_desktop_simple_git_floor_pulls_patched_argv_parser(self):
        desktop = load_json("apps/desktop/package.json")
        lock = load_json("package-lock.json")["packages"]
        self.assertGreaterEqual(parts(desktop["dependencies"]["simple-git"]), (4, 0, 2))
        self.assertGreaterEqual(
            parts(lock["node_modules/simple-git"]["version"]), (4, 0, 2)
        )
        # CVE-2026-102829 (CRITICAL) is only fixed in argv-parser >= 2.0.1 and
        # simple-git 4.0.2 is the first release requiring exactly that.
        self.assertGreaterEqual(
            parts(lock["node_modules/@simple-git/argv-parser"]["version"]),
            (2, 0, 1),
        )

    def test_root_override_floors(self):
        overrides = load_json("package.json")["overrides"]
        self.assertGreaterEqual(parts(overrides["brace-expansion"]), (5, 0, 11))
        self.assertGreaterEqual(parts(overrides["js-yaml@^4"]), (4, 3, 2))
        self.assertGreaterEqual(parts(overrides["source-map-js"]), (1, 2, 2))
        self.assertGreaterEqual(parts(overrides["undici@^6"]), (6, 29, 1))
        self.assertGreaterEqual(parts(overrides["undici@^7"]), (7, 30, 1))

    def test_root_lock_installed_floors(self):
        lock = load_json("package-lock.json")["packages"]
        self.assertGreaterEqual(
            parts(lock["node_modules/js-yaml"]["version"]), (4, 3, 2)
        )
        self.assertGreaterEqual(
            parts(lock["node_modules/brace-expansion"]["version"]), (5, 0, 11)
        )
        self.assertGreaterEqual(
            parts(lock["node_modules/source-map-js"]["version"]), (1, 2, 2)
        )
        self.assertGreaterEqual(parts(lock["node_modules/undici"]["version"]), (7, 30, 1))
        self.assertGreaterEqual(
            parts(lock["node_modules/node-gyp/node_modules/undici"]["version"]),
            (6, 29, 1),
        )

    def test_vite_floor_in_every_workspace(self):
        lock = load_json("package-lock.json")["packages"]
        for manifest in ("web", "apps/desktop", "apps/bootstrap-installer"):
            pkg = load_json(f"{manifest}/package.json")
            self.assertGreaterEqual(
                parts(pkg["devDependencies"]["vite"]), (8, 3, 3), manifest
            )
        # npm may dedupe workspace copies into the root entry; every entry that
        # exists must be at or above the floor.
        for entry, pkg in lock.items():
            if entry.endswith("node_modules/vite"):
                self.assertGreaterEqual(parts(pkg["version"]), (8, 3, 3), entry)


class ZeusStandaloneNpmSecurityFloors(unittest.TestCase):
    def test_photon_sidecar(self):
        lock = load_json("plugins/platforms/photon/sidecar/package-lock.json")["packages"]
        self.assertGreaterEqual(
            parts(lock["node_modules/@grpc/grpc-js"]["version"]), (1, 14, 5)
        )
        self.assertGreaterEqual(parts(lock["node_modules/undici"]["version"]), (7, 30, 1))

    def test_whatsapp_bridge(self):
        lock = load_json("scripts/whatsapp-bridge/package-lock.json")["packages"]
        self.assertGreaterEqual(parts(lock["node_modules/body-parser"]["version"]), (1, 20, 9))
        self.assertGreaterEqual(parts(lock["node_modules/sharp"]["version"]), (0, 35, 5))

    def test_website_floors(self):
        lock = load_json("website/package-lock.json")["packages"]
        floors = {
            "dompurify": (3, 4, 17),  # GHSA-cg2g-xh64-v4q7 (CRITICAL), GHSA-mrv2-3pqr-j5jr
            "shell-quote": (1, 11, 0),  # CVE-2026-102422 (CRITICAL)
            "proxy-addr": (2, 0, 8),  # CVE-2026-90711 (CRITICAL)
            "tinypool": (2, 1, 2),  # CVE-2026-104848/104849 (CRITICAL)
            "svgo": (3, 3, 5),  # CVE-2026-84370
            "fast-uri": (3, 1, 7),  # CVE-2026-75899/75931/75975/76172/84292
            "follow-redirects": (1, 16, 1),  # CVE-2026-111755/111756
            "browserslist": (4, 28, 7),  # CVE-2026-73088/73089
            "compression": (1, 8, 2),  # CVE-2026-87776
            "launch-editor": (2, 14, 2),  # CVE-2026-112942
            "body-parser": (1, 20, 9),  # CVE-2026-111181
            "brace-expansion": (5, 0, 11),  # CVE-2026-102276/102278
            "source-map-js": (1, 2, 2),  # CVE-2026-93749
            "js-yaml": (4, 3, 2),  # CVE-2026-84375
            "nanoid": (3, 3, 18),  # CVE-2026-67213
            "webpack-dev-middleware": (7, 4, 6),  # CVE-2026-76844
        }
        for name, floor in floors.items():
            installed = lock[f"node_modules/{name}"]["version"]
            self.assertTrue(
                at_least(installed, floor), f"website {name} {installed} < {floor}"
            )


class ZeusPythonSecurityFloors(unittest.TestCase):
    def test_pyproject_direct_pin_floors(self):
        pyproject = load_toml("pyproject.toml")
        deps = pyproject["project"]["dependencies"]

        def pin(name):
            match = [
                req for req in deps
                if re.split(r"[=<>!;\[]", req, maxsplit=1)[0].strip() == name
            ]
            self.assertTrue(match, f"{name} pin missing from core dependencies")
            return match[0]

        self.assertIn("PyJWT[crypto]==2.14.0", pin("PyJWT"))  # CVE-2026-102268 (CRITICAL)
        self.assertIn("certifi==2026.10.18", pin("certifi"))  # GHSA-6q48-6c7w-9gw2 (CRITICAL)
        self.assertIn("Pillow==12.3.0", pin("Pillow"))  # blocked: see test below
        # brotlicffi is a messaging-extra pin (brought in with aiohttp stacks).
        extras = pyproject["project"]["optional-dependencies"]
        self.assertIn("brotlicffi==1.2.1.0", extras["messaging"])  # CVE-2026-111497
        urllib3 = pin("urllib3")
        self.assertIn(">=2.8.0", urllib3)  # CVE-2026-97687/97689
        for extra in ("messaging", "matrix", "slack", "sms", "teams"):
            self.assertTrue(
                any(req.startswith("aiohttp==3.14.4") for req in extras[extra]),
                f"{extra}: aiohttp floor CVE-2026-111064/111066/GHSA-2g87-pp6c-29x5",
            )
        for extra in ("mcp", "computer-use"):
            self.assertTrue(
                any(req == "httpx2==2.10.0" for req in extras[extra]),
                f"{extra}: httpx2 floor CVE-2026-84381/84382",
            )

    def test_uv_lock_resolved_floors(self):
        versions = uv_packages()
        floors = {
            "pyjwt": (2, 14, 0),  # CVE-2026-102268 (CRITICAL)
            "certifi": (2026, 10, 18),  # GHSA-6q48-6c7w-9gw2 (CRITICAL)
            "urllib3": (2, 8, 0),  # CVE-2026-97687/97689
            "aiohttp": (3, 14, 4),  # CVE-2026-111064/111066/GHSA-2g87-pp6c-29x5
            "brotlicffi": (1, 2, 1, 0),  # CVE-2026-111497 (CRITICAL)
            "httpx2": (2, 10, 0),  # CVE-2026-84381/84382
            "httpcore2": (2, 10, 0),  # rides with httpx2
            "filelock": (4, 2, 1),  # CVE-2026-112940
            "msgpack": (1, 2, 3),  # CVE-2026-114613
            "oauthlib": (4, 0, 0),  # CVE-2026-49272
            "tornado": (6, 5, 9),  # GHSA-c2m8-h5v5-343r/GHSA-chx6-46f5-w4vp
        }
        for name, floor in floors.items():
            installed = versions[name]
            self.assertTrue(at_least(installed, floor), f"{name} {installed} < {floor}")

    def test_pillow_stays_blocked_at_browser_harness_pin(self):
        """Pillow 13.0.0 is blocked by browser-harness==0.1.13 (upstream exact pin).

        Moving Pillow silently — via an override or a partial bump — breaks the
        browser-harness contract without its author's tested floor. This test
        keeps the pairing explicit: bumping browser-harness is the release step
        that unlocks Pillow.
        """
        versions = uv_packages()
        if parts(versions["browser-harness"]) > (0, 1, 13):
            self.assertGreaterEqual(parts(versions["pillow"]), (13, 0, 0))
        else:
            self.assertEqual(versions["pillow"], "12.3.0")


if __name__ == "__main__":
    unittest.main()
