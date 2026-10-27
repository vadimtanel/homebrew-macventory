# Macventory Homebrew Tap

## About Macventory

[Macventory](https://github.com/vadimtanel/MacVentory) is a free, open-source macOS software inventory and management app by Vadim Tanel. A **Tap** is a Homebrew package-definition repository; a **Cask** is the definition that downloads and installs a macOS app. This repository is the `vadimtanel/macventory` Tap, its Cask token is `macventory`, and the application itself lives in the [main repository](https://github.com/vadimtanel/MacVentory).

## Quick Installation — One Command

With [Homebrew](https://brew.sh) installed:

```bash
brew install --cask vadimtanel/macventory/macventory
```

Homebrew discovers and adds the Tap automatically. No separate `brew tap` is needed. The fully qualified name contains the GitHub owner (`vadimtanel`), Tap name (first `macventory`) and Cask name (second `macventory`); the repetition is intentional. Homebrew downloads the official, versioned release DMG and checks its SHA-256.

## Alternative — Add Tap Manually

```bash
brew tap vadimtanel/macventory
brew install --cask vadimtanel/macventory/macventory
```

The first command adds the Tap; Homebrew resolves `vadimtanel/macventory` to [`vadimtanel/homebrew-macventory`](https://github.com/vadimtanel/homebrew-macventory). The second installs Macventory.

Fully qualified names avoid Cask-name conflicts and trust only the requested item. Adding a Tap alone does not grant trust. Under [Homebrew's Tap Trust guidance](https://docs.brew.sh/Tap-Trust), short-name installation may be used after explicitly trusting the Cask:

```bash
brew trust --cask vadimtanel/macventory/macventory
brew install --cask macventory
```

Prefer the fully qualified command; whole-Tap trust is unnecessary. Do not disable Homebrew trust checks.

## Direct Download Without Homebrew

Homebrew is optional. Download the DMG or ZIP from [official GitHub Releases](https://github.com/vadimtanel/MacVentory/releases), or go directly to the [latest stable release](https://github.com/vadimtanel/MacVentory/releases/latest). Open the DMG and drag Macventory.app to Applications, or extract the ZIP and move the app there. See the [application installation instructions](https://github.com/vadimtanel/MacVentory#installation).

## Updating

To upgrade a Homebrew-managed 1.0.0 installation to 1.1.0 (or a newer verified release available in the Tap):

```bash
brew update
brew upgrade --cask vadimtanel/macventory/macventory
```

`brew update` refreshes Homebrew metadata and Tap definitions; `brew upgrade` installs a newer version when available.

Check the available version and the installed Homebrew version with:

```bash
brew info --cask vadimtanel/macventory/macventory
brew list --cask --versions macventory
brew outdated --cask
```

`brew info` shows the available version and installed state. `brew list` reports the managed installed version and fails if the Cask is not installed. `brew outdated` lists installed Casks with newer available versions; it does not install them. A manually copied application may have no Homebrew installation record.

The [automatic updater](.github/workflows/update-cask.yml) checks official stable releases approximately every six hours, at minute 17 UTC (`00:17`, `06:17`, `12:17`, `18:17`). It verifies the published ARM64 DMG, checksum, disk-image integrity, app identity/version, architecture and signature, then runs Ruby and Homebrew checks before committing only the version and checksum. Drafts, prereleases and older releases never replace the pinned Cask. Unchanged releases create no commit; failed checks prevent publishing.

Synchronization is periodic, not instantaneous. GitHub can delay scheduled jobs and [disable public-repository schedules after 60 days of inactivity](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule). The owner can re-enable the workflow in Actions and select **Update Macventory Cask → Run workflow → main** to check immediately.

Maintainers: see [automation operation and verification](AUTOMATION.md).

The [v1.1.0 verification report](RELEASE-1.1.0.md) records official artifact provenance, checksums and distribution checks.

If an expected update is delayed, run `brew update`, check `brew info` again, then inspect the [updater runs](https://github.com/vadimtanel/homebrew-macventory/actions/workflows/update-cask.yml). A published release with a missing or incomplete DMG cannot pass verification; maintainers must finish the official upload before retrying. The owner can also trigger the workflow manually. Users should wait for a verified Tap update rather than substitute a download URL or checksum.

To uninstall the app bundle installed by this Cask:

```bash
brew uninstall --cask vadimtanel/macventory/macventory
```

This removes the managed app bundle; it does not promise to delete preferences, caches or personal data.

## System Requirements

- Apple Silicon (ARM64); the published Cask does not support Intel Macs.
- macOS 13 Ventura or later (deployment target; minimum-OS runtime remains unverified).
- Homebrew for Cask installation only; manual downloads do not require it.

## Security and Gatekeeper

Macventory is currently ad-hoc signed and **not Apple-notarized**. Homebrew does not bypass Gatekeeper, remove quarantine or approve the app's first launch. Review macOS warnings and the [project's first-launch guidance](https://github.com/vadimtanel/MacVentory#first-launch-and-gatekeeper). If you independently trust the official download, macOS may offer its per-app **System Settings → Privacy & Security → Open Anyway** process. Availability depends on macOS and organizational policy. Do not disable Gatekeeper or bypass malware/damage warnings.

A matching checksum verifies bytes; it does not independently establish publisher identity or notarization.

## License and Credits

Created by [Vadim Tanel](https://github.com/vadimtanel). Macventory and this Tap are licensed under [Apache-2.0](LICENSE). Application credits and attribution are in the [main repository](https://github.com/vadimtanel/MacVentory#license-and-credits).
