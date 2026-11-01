"""ZEUS-001/#5: Zeus-owned local install (flow B) behaviour contracts.

The installer must only operate on a verified KayzenRoot checkout (correct
origin, committed HEAD, clean tracked tree), write into an isolated root, keep
every update/bootstrap channel disabled, and uninstall exactly what its receipt
created. No test runs the real setup: the environment build is patched, so the
suite is offline and leaves no machine state behind.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "zeus_install_local.py"
FORK = "https://github.com/KayzenRoot/zeus-agent.git"


def _load_module():
    spec = importlib.util.spec_from_file_location("zeus_install_local", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves the defining module through sys.modules at class creation.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        GIT_AUTHOR_NAME="Zeus Test", GIT_AUTHOR_EMAIL="test@zeus.invalid",
        GIT_COMMITTER_NAME="Zeus Test", GIT_COMMITTER_EMAIL="test@zeus.invalid",
    )
    return env


def _repo(directory: Path, origin: str = FORK) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(directory)], check=True, env=_git_env())
    (directory / "setup-hermes.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(directory), "add", "setup-hermes.sh"], check=True, env=_git_env())
    subprocess.run(["git", "-C", str(directory), "commit", "-qm", "init"], check=True, env=_git_env())
    if origin:
        subprocess.run(["git", "-C", str(directory), "remote", "add", "origin", origin],
                       check=True, env=_git_env())
    return directory


class CheckoutVerificationTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()

    def test_non_git_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            downloaded = Path(directory)
            (downloaded / "setup-hermes.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            checkout, reason = self.module.verify_checkout(downloaded)
            self.assertIsNone(checkout)
            self.assertIn("not a git checkout", reason)

    def test_wrong_origin_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory) / "repo", origin="https://github.com/NousResearch/hermes-agent.git")
            checkout, reason = self.module.verify_checkout(repo)
            self.assertIsNone(checkout)
            self.assertIn("origin is not KayzenRoot/zeus-agent", reason)

    def test_dirty_tracked_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory) / "repo")
            (repo / "setup-hermes.sh").write_text("#!/bin/sh\n# local change\n", encoding="utf-8")
            checkout, reason = self.module.verify_checkout(repo)
            self.assertIsNone(checkout)
            self.assertIn("tracked files are modified", reason)

    def test_verified_checkout_records_head_and_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory) / "repo")
            checkout, reason = self.module.verify_checkout(repo)
            self.assertIsNone(reason)
            self.assertIsNotNone(checkout)
            self.assertEqual(checkout.origin, FORK)
            self.assertEqual(len(checkout.head), 40)


class RootValidationTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()

    def test_root_inside_the_checkout_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory) / "repo")
            checkout, _ = self.module.verify_checkout(repo)
            self.assertIn("outside the checkout",
                          self.module.validate_root(repo / "install", checkout))

    def test_existing_receipt_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory) / "repo")
            checkout, _ = self.module.verify_checkout(repo)
            root = Path(directory) / "root"
            root.mkdir()
            (root / "receipt.json").write_text("{}", encoding="utf-8")
            self.assertIn("already installed", self.module.validate_root(root, checkout))


class InstallUninstallTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()

    def _install(self, directory: Path):
        repo = _repo(directory / "repo")
        checkout, reason = self.module.verify_checkout(repo)
        self.assertIsNone(reason)
        root = directory / "installed"

        def fake_setup(active_checkout, home):
            (home / "installs").mkdir(parents=True, exist_ok=True)
            (home / "installs" / "marker").write_text("built", encoding="utf-8")
            return 0

        with mock.patch.object(self.module, "run_setup", fake_setup):
            code = self.module.install(checkout, root)
        return root, code

    def test_install_writes_receipt_launcher_and_isolated_home(self):
        with tempfile.TemporaryDirectory() as directory:
            root, code = self._install(Path(directory))
            self.assertEqual(code, 0)
            receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["kind"], "zeus-local-install")
            self.assertEqual(receipt["origin"], FORK)
            self.assertEqual(receipt["release_channel"], "local-development")
            self.assertFalse(receipt["updates_enabled"])
            self.assertEqual(Path(receipt["hermes_home"]), root / "home")
            self.assertTrue((root / "home" / "installs" / "marker").is_file())
            launcher = Path(receipt["launchers"][0])
            self.assertTrue(launcher.is_file())
            text = launcher.read_text(encoding="utf-8")
            self.assertNotIn("ZEUS_DESKTOP_BOOTSTRAP_APPROVED", text)
            self.assertNotIn("ZEUS_NATIVE_UPDATES_APPROVED", text)

    def test_failed_setup_removes_a_fresh_root(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory) / "repo")
            checkout, _ = self.module.verify_checkout(repo)
            root = Path(directory) / "installed"
            with mock.patch.object(self.module, "run_setup", lambda *_: 1):
                with self.assertRaises(RuntimeError):
                    self.module.install(checkout, root)
            self.assertFalse(root.exists(), "a failed first install must leave no partial root")

    def test_uninstall_keeps_user_data_unless_purged(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _ = self._install(Path(directory))
            sessions = root / "home" / "sessions"
            sessions.mkdir(parents=True)
            (sessions / "session.json").write_text("{}", encoding="utf-8")
            self.assertEqual(self.module.uninstall(root, confirmed=True, purge_data=False), 0)
            self.assertFalse((root / "receipt.json").exists())
            self.assertTrue(sessions.is_dir(), "sessions must survive a default uninstall")
            self.assertEqual(self.module.uninstall(root, confirmed=True, purge_data=False), 2)

    def test_uninstall_purge_removes_the_isolated_home(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _ = self._install(Path(directory))
            (root / "home" / "sessions").mkdir(parents=True)
            self.assertEqual(self.module.uninstall(root, confirmed=True, purge_data=True), 0)
            self.assertFalse(root.exists())

    def test_uninstall_without_receipt_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.module.uninstall(Path(directory), confirmed=True, purge_data=False), 2)


class CliTests(unittest.TestCase):
    def test_plan_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory) / "repo")
            root = Path(directory) / "planned"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--checkout", str(repo), "--root", str(root), "--plan"],
                capture_output=True, text=True, timeout=60, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("checkout:", result.stdout)
            self.assertIn("isolated HERMES_HOME", result.stdout)
            self.assertFalse(root.exists(), "--plan must not create the install root")

    def test_cli_refuses_a_wrong_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = _repo(Path(directory) / "repo", origin="https://github.com/NousResearch/hermes-agent.git")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--checkout", str(repo),
                 "--root", str(Path(directory) / "planned"), "--plan"],
                capture_output=True, text=True, timeout=60, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("zeus-release-unapproved", result.stderr)


if __name__ == "__main__":
    unittest.main()
