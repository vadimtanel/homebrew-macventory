import copy
import hashlib
import importlib.util
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("updater", ROOT / "scripts/update_cask.py")
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
PAYLOAD = b"mock-dmg" + b"koly" + bytes(508)
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


def release(version="1.0.1"):
    return {"draft": False, "prerelease": False, "published_at": "2026-10-24T12:00:00Z",
            "tag_name": "v" + version, "assets": [{"name": f"Macventory-{version}-arm64.dmg",
            "browser_download_url": f"{u.BASE}/v{version}/Macventory-{version}-arm64.dmg",
            "state": "uploaded", "size": len(PAYLOAD), "digest": "sha256:" + DIGEST}]}


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cask = Path(self.temp.name) / "macventory.rb"
        self.original = u.TEMPLATE.format(version="1.0.0", sha256="0" * 64)
        self.cask.write_text(self.original)

    def invoke(self, data=None, download_error=None, inspect_error=None, verify_current=False):
        def download(asset, path):
            if download_error:
                raise download_error
            path.write_bytes(PAYLOAD)
        with patch.object(u, "fetch_release", return_value=data or release()), \
             patch.object(u, "download", side_effect=download), \
             patch.object(u, "inspect_dmg", side_effect=inspect_error) as inspect:
            result = u.update(self.cask, verify_current)
        return result, inspect.call_count

    def test_new_stable_changes_only_version_and_digest(self):
        result, calls = self.invoke()
        self.assertTrue(result["changed"])
        self.assertEqual(calls, 1)
        self.assertEqual(self.cask.read_text(),
                         self.original.replace('version "1.0.0"', 'version "1.0.1"')
                         .replace('"' + "0" * 64 + '"', '"' + DIGEST + '"'))
        second, calls = self.invoke()
        self.assertFalse(second["changed"])
        self.assertEqual(calls, 0)

    def test_initial_same_version_and_repeated_noop(self):
        for _ in range(2):
            result, calls = self.invoke(release("1.0.0"))
            self.assertFalse(result["changed"])
            self.assertEqual(calls, 0)
        self.assertEqual(self.cask.read_text(), self.original)

    def test_older_release(self):
        self.assertFalse(self.invoke(release("0.9.9"))[0]["changed"])

    def test_numeric_version_comparison(self):
        self.assertEqual(u.choose_release(release("1.0.10"), "1.0.9")[0], "1.0.10")

    def test_future_stable_versions_from_110(self):
        for version in ("1.1.1", "1.2.0", "2.0.0"):
            with self.subTest(version=version):
                self.cask.write_text(u.TEMPLATE.format(version="1.1.0", sha256="0" * 64))
                result, calls = self.invoke(release(version), verify_current=True)
                self.assertEqual(result["version"], version)
                self.assertTrue(result["changed"])
                self.assertEqual(calls, 1)
                self.assertEqual(u.read_cask(self.cask)[1:], (version, DIGEST))
                self.assertFalse(self.invoke(release(version), verify_current=True)[0]["changed"])

    def test_future_release_uses_new_checksum_and_never_downgrades(self):
        self.cask.write_text(u.TEMPLATE.format(version="1.1.0", sha256=DIGEST))
        payload = b"new-release" + b"koly" + bytes(508)
        digest = hashlib.sha256(payload).hexdigest()
        data = release("1.2.0")
        data["assets"][0].update(size=len(payload), digest="sha256:" + digest)
        with patch.object(u, "fetch_release", return_value=data), \
             patch.object(u, "download", side_effect=lambda a, p: p.write_bytes(payload)), \
             patch.object(u, "inspect_dmg"):
            self.assertTrue(u.update(self.cask, verify_current=True)["changed"])
        self.assertEqual(u.read_cask(self.cask)[1:], ("1.2.0", digest))
        updated = self.cask.read_text()
        self.assertFalse(self.invoke(release("1.1.1"))[0]["changed"])
        self.assertEqual(self.cask.read_text(), updated)

    def test_published_110_without_assets_keeps_100(self):
        data = release("1.1.0")
        data["assets"] = []
        with patch.object(u, "fetch_release", return_value=data), \
             patch.object(u, "download") as download:
            with self.assertRaisesRegex(ValueError, "Macventory-1.1.0-arm64.dmg"):
                u.update(self.cask, verify_current=True)
        download.assert_not_called()
        self.assertEqual(self.cask.read_text(), self.original)

    def test_prerelease_and_draft_ignored(self):
        for flag in ("prerelease", "draft"):
            data = release("1.1.0-beta.1")
            data[flag] = True
            self.assertFalse(self.invoke(data)[0]["changed"])

    def test_invalid_tags_fail(self):
        for tag in ("1.0.1", "v01.0.1", "v1.1.0-beta.1", "v1.0.1\n", "v1.0.1;id"):
            with self.subTest(tag=tag):
                data = release()
                data["tag_name"] = tag
                with self.assertRaisesRegex(ValueError, "tag"):
                    self.invoke(data)
                self.assertEqual(self.cask.read_text(), self.original)

    def test_missing_duplicate_or_incomplete_dmg(self):
        for assets in ([], release()["assets"] * 2,
                       [dict(release()["assets"][0], state="new")]):
            data = release()
            data["assets"] = assets
            with self.assertRaises(ValueError):
                self.invoke(data)
            self.assertEqual(self.cask.read_text(), self.original)

    def test_suspicious_asset_metadata(self):
        for change in ({"browser_download_url": "https://evil.example/release.dmg"},
                       {"size": 0}, {"size": u.MAX_BYTES + 1}, {"size": True},
                       {"digest": "md5:123"}, {"digest": "sha256:" + "f" * 64}):
            data = release()
            data["assets"][0].update(change)
            with self.assertRaises(ValueError):
                self.invoke(data)
            self.assertEqual(self.cask.read_text(), self.original)

    def test_download_and_api_failures_retain_cask(self):
        with self.assertRaisesRegex(OSError, "network unavailable"):
            self.invoke(download_error=OSError("network unavailable"))
        with patch.object(u, "fetch_release", side_effect=OSError("API unavailable")):
            with self.assertRaisesRegex(OSError, "API unavailable"):
                u.update(self.cask)
        self.assertEqual(self.cask.read_text(), self.original)

    def test_integrity_app_or_signature_failure_retain_cask(self):
        for error in ("invalid DMG", "missing app", "wrong version", "wrong architecture",
                      "wrong bundle identifier", "invalid signature"):
            with self.assertRaisesRegex(ValueError, error):
                self.invoke(inspect_error=ValueError(error))
            self.assertEqual(self.cask.read_text(), self.original)

    def test_same_version_revalidation_detects_replaced_asset(self):
        with self.assertRaisesRegex(ValueError, "pinned Cask"):
            self.invoke(release("1.0.0"), verify_current=True)
        self.cask.write_text(u.TEMPLATE.format(version="1.0.0", sha256=DIGEST))
        self.assertFalse(self.invoke(release("1.0.0"), verify_current=True)[0]["changed"])

    def test_digest_optional_but_download_still_verified(self):
        data = release()
        data["assets"][0]["digest"] = None
        self.assertTrue(self.invoke(data)[0]["changed"])

    def test_missing_publication_flags_and_date(self):
        for key in ("published_at", "draft", "prerelease"):
            data = release()
            del data[key]
            with self.assertRaises(ValueError):
                self.invoke(data)

    def test_unexpected_cask_structure_is_rejected(self):
        self.cask.write_text(self.original + "# unexpected change\n")
        with self.assertRaisesRegex(ValueError, "structure"):
            self.invoke()

    def test_empty_truncated_and_non_dmg_bytes(self):
        path = self.cask.parent / "invalid.dmg"
        asset = release()["assets"][0]
        for payload in (b"", PAYLOAD[:-1], b"x" * len(PAYLOAD)):
            path.write_bytes(payload)
            with self.assertRaises(ValueError):
                u.verify_bytes(path, asset)

    def test_app_inspection_checks_actual_plist_and_architecture(self):
        app = self.cask.parent / "Macventory.app"
        (app / "Contents/MacOS").mkdir(parents=True)
        executable = app / "Contents/MacOS/Macventory"
        executable.write_bytes(b"binary fixture")
        info = {"CFBundleIdentifier": "org.vadimtanel.Macventory",
                "CFBundleExecutable": "Macventory", "CFBundleName": "Macventory",
                "CFBundlePackageType": "APPL", "CFBundleShortVersionString": "1.0.1",
                "LSMinimumSystemVersion": "13.0"}
        plist = app / "Contents/Info.plist"
        plist.write_bytes(plistlib.dumps(info))
        with patch.object(u, "run", side_effect=[b"arm64\n", b""]):
            u.inspect_app(app, "1.0.1")
        for key in info:
            bad = copy.copy(info)
            bad[key] = "unexpected"
            plist.write_bytes(plistlib.dumps(bad))
            with self.assertRaisesRegex(ValueError, key):
                u.inspect_app(app, "1.0.1")
        plist.write_bytes(plistlib.dumps(info))
        with patch.object(u, "run", return_value=b"x86_64\n"):
            with self.assertRaisesRegex(ValueError, "ARM64"):
                u.inspect_app(app, "1.0.1")

    def test_detach_on_app_failure(self):
        def command(*args):
            if args[1] == "attach":
                mount = args[args.index("-mountpoint") + 1]
                return plistlib.dumps({"system-entities": [{"mount-point": mount}]})
            return b""
        with patch.object(u, "run", side_effect=command) as run, \
             patch.object(u, "inspect_app", side_effect=ValueError("bad app")):
            with self.assertRaisesRegex(ValueError, "bad app"):
                u.inspect_dmg(Path("fixture.dmg"), "1.0.1")
            self.assertEqual(run.call_args.args[1], "detach")


class PublicationTests(unittest.TestCase):
    def git(self, cwd, *args):
        return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def test_stale_main_and_remote_rejection_cannot_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "origin.git"
            self.git(root, "init", "--bare", str(remote))
            checkout = root / "checkout"
            self.git(root, "clone", str(remote), str(checkout))
            self.git(checkout, "checkout", "-b", "main")
            self.git(checkout, "config", "user.name", "Test")
            self.git(checkout, "config", "user.email", "test@example.com")
            (checkout / "Casks").mkdir()
            cask = checkout / "Casks/macventory.rb"
            cask.write_text(u.TEMPLATE.format(version="1.1.0", sha256="0" * 64))
            self.git(checkout, "add", ".")
            self.git(checkout, "commit", "-m", "initial")
            self.git(checkout, "push", "origin", "main")
            initial = self.git(checkout, "rev-parse", "HEAD")
            cask.write_text(u.TEMPLATE.format(version="1.1.1", sha256=DIGEST))
            # A server-side refusal must leave remote main unchanged.
            hook = remote / "hooks/pre-receive"
            hook.write_text("#!/bin/sh\necho 'test publication denied' >&2\nexit 1\n")
            hook.chmod(0o755)
            publisher = ROOT / "scripts/publish_cask.sh"
            result = subprocess.run(["bash", str(publisher), "1.1.1"], cwd=checkout,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("test publication denied", result.stderr)
            self.assertEqual(self.git(remote, "rev-parse", "main"), initial)
            # A retry from a stale local commit is refused before another commit.
            cask.write_text(u.TEMPLATE.format(version="1.2.0", sha256=DIGEST))
            local = self.git(checkout, "rev-parse", "HEAD")
            result = subprocess.run(["bash", str(publisher), "1.2.0"], cwd=checkout,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Remote main changed", result.stderr)
            self.assertEqual(self.git(checkout, "rev-parse", "HEAD"), local)
            self.assertEqual(self.git(remote, "rev-parse", "main"), initial)

    def test_two_stale_publishers_create_at_most_one_remote_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "origin.git"
            self.git(root, "init", "--bare", str(remote))
            first = root / "first"
            self.git(root, "clone", str(remote), str(first))
            self.git(first, "checkout", "-b", "main")
            self.git(first, "config", "user.name", "Test")
            self.git(first, "config", "user.email", "test@example.com")
            (first / "Casks").mkdir()
            cask = first / "Casks/macventory.rb"
            cask.write_text(u.TEMPLATE.format(version="1.0.0", sha256="0" * 64))
            self.git(first, "add", "Casks/macventory.rb")
            self.git(first, "commit", "-m", "initial")
            self.git(first, "push", "origin", "main")
            second = root / "second"
            self.git(root, "clone", "--branch", "main", str(remote), str(second))
            for checkout in (first, second):
                (checkout / "Casks/macventory.rb").write_text(
                    u.TEMPLATE.format(version="1.0.1", sha256=DIGEST))
            publisher = ROOT / "scripts/publish_cask.sh"
            processes = [subprocess.Popen(["bash", str(publisher), "1.0.1"], cwd=p,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE) for p in (first, second)]
            for p in processes:
                p.communicate(timeout=30)
            # Identical same-second commits can share a SHA, in which case
            # both normal pushes succeed while publishing only one commit.
            self.assertTrue(any(p.returncode == 0 for p in processes))
            self.assertTrue(all(p.returncode in (0, 1) for p in processes))
            self.assertEqual(self.git(remote, "rev-list", "--count", "main"), "2")
            # A new checkout already at the update must not create another commit.
            third = root / "third"
            self.git(root, "clone", "--branch", "main", str(remote), str(third))
            subprocess.run(["bash", str(publisher), "1.0.1"], cwd=third, check=True,
                           capture_output=True)
            self.assertEqual(self.git(remote, "rev-list", "--count", "main"), "2")
            (third / "unrelated.txt").write_text("keep")
            result = subprocess.run(["bash", str(publisher), "1.0.1"], cwd=third,
                                    capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(self.git(remote, "rev-list", "--count", "main"), "2")


if __name__ == "__main__":
    unittest.main()
