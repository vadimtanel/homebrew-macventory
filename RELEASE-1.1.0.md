# v1.1.0 release verification and recovery

## Publication is blocked

On 27 October 2026 the official latest stable release was [v1.1.0](https://github.com/vadimtanel/MacVentory/releases/tag/v1.1.0), release ID `425765148`, with `draft=false`, `prerelease=false` and **zero uploaded assets**. These four files were all missing:

- `Macventory-1.1.0-arm64.dmg`
- `Macventory-1.1.0-arm64.zip`
- `Macventory-1.1.0-arm64.sha256`
- `Macventory-1.1.0-source.tar.gz`

The production Cask consequently remains **1.0.0**, with its existing checksum `b7a2a64c5a5a17667e933195d383f0782d6b4ae27e8b27d39df76b65382bbcbf`. There is no verified official-download checksum for 1.1.0 yet. The candidate checksum below is not authority to update the Cask before the official upload.

## Verified candidate provenance

The tag resolves directly to commit [`54bb40270bf8309ce454cfb0cf73c80afed07ef9`](https://github.com/vadimtanel/MacVentory/commit/54bb40270bf8309ce454cfb0cf73c80afed07ef9). Its [CI run 40535995628](https://github.com/vadimtanel/MacVentory/actions/runs/40535995628) succeeded for both the native build/package validation and the full synthetic GUI suite.

Use that run's `verification-arm64` artifact, ID `12747368771`, rather than older local or branch candidates. Its downloaded ZIP has SHA-256 `0593f66fd4e676e78893666b973e1a282ec3db767db7234231a249fa7af1ae83`. It expires on 10 November 2026; retain an approved verified copy before then. The four release files are under `artifacts/` inside it.

Independent local validation of these exact candidate bytes confirmed:

- All three file digests match the included `.sha256` list.
- All 151 source-archive files match Git blob hashes at the tagged commit; there are no additional or missing files.
- `hdiutil verify` passes; the DMG mounts read-only and is detached after inspection.
- The DMG contains `Macventory.app` and an `Applications` link to `/Applications`.
- All 10 app files in the ZIP match the mounted DMG app byte for byte.
- Bundle identifier `org.vadimtanel.Macventory`, version **1.1.0**, build **108**, minimum macOS **13.0**.
- The app executable and `MacventoryPrivilegedHelper` are both ARM64 and pass strict signature verification; the app also passes deep strict verification.
- Signing is ad-hoc, with no Team ID. These checks do not establish Developer ID, notarization or macOS 13 runtime compatibility.

| Candidate file | Bytes | SHA-256 |
| --- | ---: | --- |
| `Macventory-1.1.0-arm64.dmg` | 4269317 | `183dd721cdda80de376ce114b080729afac763e33fccb4354045cef576842e36` |
| `Macventory-1.1.0-arm64.zip` | 3954744 | `2dbb58e4763108f2e9872a2b32de7ec5cc6c938f342c9e3db29ebe7c576c0140` |
| `Macventory-1.1.0-source.tar.gz` | 5823172 | `7b0714e1e1bfb05020e481de40e8d18a5faf22b8f66b5934bddb0a0c8e364c59` |

## Upload procedure — owner approval required

Do not execute the upload until the owner approves these exact four candidate files. No app rebuild, tag change or replacement of existing release assets is needed. Use an authenticated GitHub CLI with permission to upload application release assets, and obtain the artifact above from the successful run. Extract it into a disposable directory, verify the outer ZIP checksum, then enter its `artifacts/` directory (or use the prepared candidate directory provided in the verification report).

Immediately before uploading, recheck that the tag is unchanged, the latest release is still 1.1.0, and all four filenames are still absent. Stop if any check differs; verify newly uploaded files instead of overwriting them. From the directory containing the four verified files:

```bash
set -euo pipefail
test "$(gh api repos/vadimtanel/MacVentory/git/ref/tags/v1.1.0 --jq .object.sha)" = 54bb40270bf8309ce454cfb0cf73c80afed07ef9
test "$(gh api repos/vadimtanel/MacVentory/releases/latest --jq .tag_name)" = v1.1.0
test "$(gh api repos/vadimtanel/MacVentory/releases/tags/v1.1.0 --jq .id)" = 425765148
test "$(gh api repos/vadimtanel/MacVentory/releases/tags/v1.1.0 --jq '.assets | length')" = 0
shasum -a 256 -c Macventory-1.1.0-arm64.sha256
gh release upload v1.1.0 --repo vadimtanel/MacVentory \
  Macventory-1.1.0-arm64.dmg Macventory-1.1.0-arm64.zip \
  Macventory-1.1.0-arm64.sha256 Macventory-1.1.0-source.tar.gz
```

The upload command intentionally omits `--clobber`. If an upload partially fails, inspect the official uploaded assets and compare their digests before uploading only the missing files. Re-run the Tap updater only after all four files are present and the public DMG download succeeds.

## Finish the Tap upgrade after upload

1. Download the DMG from the exact public URL `https://github.com/vadimtanel/MacVentory/releases/download/v1.1.0/Macventory-1.1.0-arm64.dmg`. Verify its SHA-256 and app contents against the approved candidate.
2. Dispatch **Update Macventory Cask** on `main`. The existing updater discovers 1.1.0, independently downloads and inspects its official DMG, prepares the version/checksum, runs regression/Ruby/Homebrew checks, then uses its guarded fast-forward publication script. No manual Cask edit is necessary.
3. Confirm the hosted run passed and the bot commit changed only `Casks/macventory.rb`. Check version, URL and checksum using `brew info --json=v2 --cask vadimtanel/macventory/macventory` and `scripts/check_cask_info.py`.
4. In a disposable macOS runner, validate a fresh install and an upgrade from a separately installed official 1.0.0 Cask. Verify installed bundle version 1.1.0/build 108 and that `brew outdated --cask` no longer reports Macventory. Do not overwrite an owner's application or invoke removal/cleanup features.
5. Remove the dated README availability warning only after verified publication. Record the bot commit and install/upgrade evidence, then remove disposable QA files and mounts.

Until those steps pass, fresh 1.1.0 installation and upgrade remain **blocked**, not verified. Mocked future-version tests and a successful `Validate Tap` run do not substitute for the official release DMG or installation evidence.
