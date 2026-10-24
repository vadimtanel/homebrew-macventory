#!/usr/bin/env python3
"""Verify an official stable release before atomically updating the pinned Cask.

No third-party Python packages. Never installs or executes the downloaded app.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import tempfile
import urllib.request

API = "https://api.github.com/repos/vadimtanel/MacVentory/releases/latest"
BASE = "https://github.com/vadimtanel/MacVentory/releases/download"
VERSION = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
MAX_BYTES = 512 * 1024 * 1024
CASK = Path(__file__).resolve().parents[1] / "Casks/macventory.rb"
TEMPLATE = '''cask "macventory" do
  version "{version}"
  sha256 "{sha256}"

  url "https://github.com/vadimtanel/MacVentory/releases/download/v#{{version}}/Macventory-#{{version}}-arm64.dmg"
  name "Macventory"
  desc "Software inventory and management"
  homepage "https://github.com/vadimtanel/MacVentory"

  depends_on arch: :arm64
  depends_on macos: :ventura

  app "Macventory.app"
end
'''


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(*args):
    result = subprocess.run(args, check=False, capture_output=True, timeout=180)
    require(result.returncode == 0,
            f"{args[0]} {args[1]} failed: "
            + result.stderr.decode(errors="replace")[-2000:])
    return result.stdout


def read_cask(path):
    original = path.read_text()
    versions = re.findall(r'^  version "(' + VERSION + r')"$', original, re.M)
    sums = re.findall(r'^  sha256 "([0-9a-f]{64})"$', original, re.M)
    require(len(versions) == len(sums) == 1, "Cask version/checksum structure is unexpected")
    require(original == TEMPLATE.format(version=versions[0], sha256=sums[0]),
            "Cask structure differs from the reviewed template; review updater before proceeding")
    return original, versions[0], sums[0]


def fetch_release():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "macventory-cask-updater",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(API, headers=headers), timeout=30) as response:
        require(response.url == API, "Unexpected release API redirect")
        raw = response.read(2 * 1024 * 1024 + 1)
    require(len(raw) <= 2 * 1024 * 1024, "Oversized API response")
    return json.loads(raw)


def choose_release(release, current):
    require(isinstance(release, dict), "Release response is not an object")
    # Missing flags must not accidentally authorize publication.
    require(type(release.get("draft")) is bool and type(release.get("prerelease")) is bool,
            "Release publication flags missing or invalid")
    if release["draft"] or release["prerelease"]:
        return None
    require(isinstance(release.get("published_at"), str) and release["published_at"],
            "Release is not published")
    tag = release.get("tag_name")
    require(isinstance(tag, str) and re.fullmatch("v" + VERSION, tag),
            "Stable release tag must be vMAJOR.MINOR.PATCH without leading zeroes")
    version = tag[1:]
    if tuple(map(int, version.split("."))) < tuple(map(int, current.split("."))):
        return None
    name = f"Macventory-{version}-arm64.dmg"
    assets = release.get("assets")
    require(isinstance(assets, list) and all(isinstance(a, dict) for a in assets),
            "Release assets missing or invalid")
    matches = [a for a in assets if a.get("name") == name]
    require(len(matches) == 1, "Expected exactly one published asset: " + name)
    asset = matches[0]
    require(asset.get("state") == "uploaded", "DMG asset is not fully uploaded")
    require(asset.get("browser_download_url") == f"{BASE}/{tag}/{name}",
            "DMG URL is not the exact official versioned release URL")
    require(type(asset.get("size")) is int and 0 < asset["size"] <= MAX_BYTES,
            "DMG size is empty, missing or exceeds 512 MiB")
    digest = asset.get("digest")
    require(digest is None or (isinstance(digest, str)
                              and re.fullmatch(r"sha256:[0-9a-f]{64}", digest)),
            "Unsupported or invalid GitHub asset digest")
    return version, asset


def download(asset, destination):
    # GitHub may redirect to its release CDN. TLS remains required at every hop;
    # no API token is sent to the asset URL or redirect destinations.
    run("curl", "--fail", "--silent", "--show-error", "--location", "--max-redirs", "5",
        "--proto", "=https", "--proto-redir", "=https", "--connect-timeout", "30",
        "--max-time", "180", "--max-filesize", str(MAX_BYTES),
        "--output", str(destination), asset["browser_download_url"])


def verify_bytes(path, asset):
    require(path.is_file() and path.stat().st_size == asset["size"],
            "Downloaded DMG size differs from published size")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    require(asset.get("digest") is None or asset["digest"] == "sha256:" + digest,
            "Downloaded DMG SHA-256 differs from GitHub digest")
    with path.open("rb") as stream:
        require(path.stat().st_size >= 512, "DMG is too small")
        stream.seek(-512, 2)
        require(stream.read(4) == b"koly", "Downloaded file is not a UDIF disk image")
    return digest


def inside(path, parent):
    require(path.resolve().is_relative_to(parent.resolve()), "App path escapes its bundle")
    return path


def inspect_app(app, version):
    require(app.is_dir() and not app.is_symlink(), "Expected Macventory.app is missing or linked")
    plist = inside(app / "Contents/Info.plist", app)
    with plist.open("rb") as stream:
        info = plistlib.load(stream)
    for key, value in {"CFBundleIdentifier": "org.vadimtanel.Macventory",
                       "CFBundleExecutable": "Macventory", "CFBundleName": "Macventory",
                       "CFBundlePackageType": "APPL", "CFBundleShortVersionString": version,
                       "LSMinimumSystemVersion": "13.0"}.items():
        require(info.get(key) == value, f"App identity/version mismatch: {key}")
    executable = inside(app / "Contents/MacOS/Macventory", app)
    require(executable.is_file(), "App executable is missing")
    require(run("lipo", "-archs", str(executable)).decode().strip() == "arm64",
            "App executable must be ARM64")
    run("codesign", "--verify", "--deep", "--strict", str(app))


def inspect_dmg(path, version):
    run("hdiutil", "verify", str(path))
    with tempfile.TemporaryDirectory(prefix="macventory-mount-") as directory:
        mount = Path(directory) / "volume"
        mount.mkdir()
        # -plist makes attachment output machine-readable; no Finder or app launch.
        attached = False
        try:
            output = run("hdiutil", "attach", "-readonly", "-nobrowse", "-noautoopen",
                         "-plist", "-mountpoint", str(mount), str(path))
            attached = True
            entities = plistlib.loads(output).get("system-entities", [])
            require(any(Path(e["mount-point"]).resolve() == mount.resolve()
                        for e in entities if e.get("mount-point")),
                    "DMG did not mount at the isolated inspection path")
            inspect_app(mount / "Macventory.app", version)
        finally:
            if attached:
                run("hdiutil", "detach", str(mount))


def update(path=CASK, verify_current=False):
    original, current, old_digest = read_cask(path)
    selected = choose_release(fetch_release(), current)
    if selected is None:
        return {"changed": False, "version": current, "reason": "draft, prerelease or older release"}
    version, asset = selected
    if version == current and not verify_current:
        return {"changed": False, "version": current, "reason": "already current"}
    with tempfile.TemporaryDirectory(prefix="macventory-release-") as directory:
        dmg = Path(directory) / "release.dmg"
        download(asset, dmg)
        digest = verify_bytes(dmg, asset)
        inspect_dmg(dmg, version)
    if version == current:
        require(digest == old_digest, "Current release DMG no longer matches pinned Cask checksum")
        return {"changed": False, "version": current, "reason": "current artifact verified"}
    revised = TEMPLATE.format(version=version, sha256=digest)
    require(path.read_text() == original, "Cask changed during validation; refusing to overwrite")
    # Atomic replacement occurs only after every artifact check has passed.
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(revised)
    try:
        temporary.chmod(0o644)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return {"changed": True, "version": version, "reason": "new stable release verified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-current", action="store_true",
                        help="also inspect the unchanged release without committing")
    args = parser.parse_args()
    result = update(verify_current=args.verify_current)
    print(json.dumps(result))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            stream.write(f'changed={str(result["changed"]).lower()}\nversion={result["version"]}\n')


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Cask update failed: {error}", file=sys.stderr)
        sys.exit(1)
