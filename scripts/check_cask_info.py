#!/usr/bin/env python3
"""Check that Homebrew loaded the reviewed version, URL, checksum and artifact."""
import json
from pathlib import Path
import sys

from update_cask import BASE, read_cask, require

_, version, digest = read_cask(Path(__file__).resolve().parents[1] / "Casks/macventory.rb")
with open(sys.argv[1]) as stream:
    casks = json.load(stream)["casks"]
require(len(casks) == 1, "Expected exactly one loaded Cask")
cask = casks[0]
require(cask["token"] == "macventory", "Unexpected Cask token")
require(cask["version"] == version, "Loaded Cask version mismatch")
require(cask["sha256"] == digest, "Loaded Cask checksum mismatch")
require(cask["url"] == f"{BASE}/v{version}/Macventory-{version}-arm64.dmg",
        "Loaded Cask URL/version mismatch")
require(any(a.get("app") == ["Macventory.app"] for a in cask["artifacts"]),
        "Expected app artifact missing")
print("Homebrew Cask version, URL, checksum and app artifact verified")
