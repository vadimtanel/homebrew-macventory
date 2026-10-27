# Macventory v1.1.0 distribution verification

## Published release

Verified on 27 October 2026: the official latest stable [v1.1.0 release](https://github.com/vadimtanel/MacVentory/releases/tag/v1.1.0), release ID `425765148`, contains all four required uploaded assets. The owner approved the exact verified files before upload. They were attached through the existing release editor; no application code, tag, release version or release notes were changed.

The tag remains at validated commit [`54bb40270bf8309ce454cfb0cf73c80afed07ef9`](https://github.com/vadimtanel/MacVentory/commit/54bb40270bf8309ce454cfb0cf73c80afed07ef9). All four public downloads matched the approved files byte for byte and matched GitHub's asset digests.

| Official asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Macventory-1.1.0-arm64.dmg` | 4269317 | `183dd721cdda80de376ce114b080729afac763e33fccb4354045cef576842e36` |
| `Macventory-1.1.0-arm64.zip` | 3954744 | `2dbb58e4763108f2e9872a2b32de7ec5cc6c938f342c9e3db29ebe7c576c0140` |
| `Macventory-1.1.0-arm64.sha256` | 283 | `b8f8d80269ed92e63fc1aeb5e62bc3fbba2e5204444d2f8c307c72849c06f956` |
| `Macventory-1.1.0-source.tar.gz` | 5823172 | `7b0714e1e1bfb05020e481de40e8d18a5faf22b8f66b5934bddb0a0c8e364c59` |

The Cask pins **1.1.0** and the DMG checksum above. Its resolved URL is:

```text
https://github.com/vadimtanel/MacVentory/releases/download/v1.1.0/Macventory-1.1.0-arm64.dmg
```

## Artifact provenance and validation

The files were recovered from the successful application [CI run 40535995628](https://github.com/vadimtanel/MacVentory/actions/runs/40535995628) at the exact tag commit. Its native build/package checks and full synthetic GUI suite passed. The `verification-arm64` artifact ID was `12747368771`; the downloaded artifact container had SHA-256 `0593f66fd4e676e78893666b973e1a282ec3db767db7234231a249fa7af1ae83`.

Independent candidate checks and subsequent official-download verification established:

- All three packaged-file hashes match the included checksum list.
- All 151 source-archive files match Git blob hashes at the tagged commit, with no additional or missing files.
- Disk-image integrity verification passes; inspection mounts were read-only and detached afterward.
- The DMG contains `Macventory.app` and an `Applications` link to `/Applications`.
- All 10 app files in the ZIP match the mounted DMG app byte for byte.
- Bundle identifier `org.vadimtanel.Macventory`, version **1.1.0**, build **108**, minimum macOS **13.0**.
- The app and `MacventoryPrivilegedHelper` executables are ARM64 and pass strict code-signature verification; the app also passes deep strict verification.
- Signing is ad-hoc, with no Team ID. No notarization or Gatekeeper bypass was introduced.

## Tap publication and repeat verification

The existing [Update Macventory Cask run 40571317556](https://github.com/vadimtanel/homebrew-macventory/actions/runs/40571317556) discovered and independently verified the official DMG, passed all **22 regression tests**, Ruby syntax, Homebrew Cask metadata/URL/checksum checks, online audit and style. It published [bot commit `ca5b72dab772fa4e248b8e7512114e7b1448b870`](https://github.com/vadimtanel/homebrew-macventory/commit/ca5b72dab772fa4e248b8e7512114e7b1448b870), changing only the Cask version and checksum.

A [repeat run 40571954801](https://github.com/vadimtanel/homebrew-macventory/actions/runs/40571954801) passed the same checks, returned `{"changed": false, "version": "1.1.0", "reason": "current artifact verified"}` and skipped the commit/push step. Publication used the existing same-repository `GITHUB_TOKEN`, guarded fast-forward push and concurrency group. No PAT, force push or protection bypass was used.

Read-only local Homebrew metadata validation also resolved version 1.1.0, the exact official URL and the matching checksum. The local Tap checkout was advanced to the bot commit with a fast-forward merge; no local app installation was changed.

## Fresh installation and upgrade evidence

[Installation verification run 40571886778](https://github.com/vadimtanel/homebrew-macventory/actions/runs/40571886778) passed both independent disposable macOS 15 ARM64 jobs:

| Job | Verified behavior |
| --- | --- |
| Fresh installation | The fully qualified Cask installed the official 1.1.0 app into a runner temporary application folder. |
| Upgrade | Installed the official 1.0.0 Cask from historical Tap commit `2a95a3e3a5465a1b7f8c367a18480b964e7c2a81`, ran `brew update`, required Macventory to appear in `brew outdated --cask`, then successfully ran `brew upgrade --cask`. The log records `1.0.0 -> 1.1.0`. |

Both jobs verified installed **1.1.0/build 108**, bundle identity, minimum-OS metadata, ARM64 architecture and signature integrity. `brew info` matched the reviewed Cask version, download URL, SHA-256 and app artifact; `brew list --cask --versions macventory` reported `macventory 1.1.0`. Macventory was absent from `brew outdated --cask` afterward.

The jobs used `--appdir="$RUNNER_TEMP/macventory-apps"` to isolate the destination. The app was never launched, and no Macventory removal or cleanup feature was exercised. The owner's application and package installations were untouched. The manual workflow can reproduce this specific release acceptance check on disposable runners.

## Future stable updates

The existing updater was retained. It checks approximately every six hours and supports manual dispatch on `main`. Tests explicitly cover 1.1.1, 1.2.0 and 2.0.0 discovery from 1.1.0, changed checksums, repeated verification, numeric ordering, draft/prerelease rejection, missing/incomplete assets, verification failures, rejected publication and concurrent publishers. Older releases cannot replace newer ones; failed verification cannot publish a changed Cask.

Future version numbers require no updater rewrite. Changes to reviewed packaging, bundle identity, architecture or minimum OS still require maintainer review. Discovery is periodic, not instantaneous. User installation, upgrade, version-check and troubleshooting commands are documented in [README.md](README.md), with maintainer procedures in [AUTOMATION.md](AUTOMATION.md).

## Safe failure before the approved upload

Initially the published release had zero uploaded assets. The live updater refused it with `Expected exactly one published asset: Macventory-1.1.0-arm64.dmg` and left the 1.0.0 Cask unchanged. The earlier [validation run 40553415345](https://github.com/vadimtanel/homebrew-macventory/actions/runs/40553415345) passed regression, Ruby and metadata checks but correctly failed online audit because livecheck saw 1.1.0 while the Cask remained 1.0.0. Publication stayed blocked until owner-approved, verified assets were public. The successful publication and repeat runs above resolve that blocker without suppressing any validation.

## Scope, cleanup and limits

Changed files: `Casks/macventory.rb`, `README.md`, `AUTOMATION.md`, `RELEASE-1.1.0.md`, `tests/test_updater.py`, `.github/workflows/validate.yml`, and `.github/workflows/install-check.yml`. The updater and publisher implementation and six-hour schedule remain unchanged.

Temporary local public-download copies, Homebrew test caches/logs and metadata files were removed. Inspection disk images were detached. GitHub discarded the disposable runners and their test installations. Prepared release files and publication screenshots are retained as deliverables, not temporary QA installations. Unrelated pre-existing local files were preserved.

No distribution blocker remains. The app remains ad-hoc signed and not Apple-notarized; macOS 13 is the configured deployment minimum, with macOS 13 runtime compatibility still unverified. These limitations are preserved in the user documentation.
