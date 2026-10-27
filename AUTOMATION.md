# Maintaining the release updater

The workflow `.github/workflows/update-cask.yml` runs on macOS every six hours (`17 */6 * * *`, UTC) and supports manual execution on `main`. It queries the fixed official `/releases/latest` API endpoint, accepts only published stable `vMAJOR.MINOR.PATCH` releases, and compares numeric versions. It never follows arbitrary tags, installs the application, or launches downloaded code.

## Validation and publication

`scripts/update_cask.py` requires the exact versioned official ARM64 DMG URL and one fully uploaded, nonempty asset. Downloads use HTTPS, bounded size/time and isolated temporary paths. The updater calculates SHA-256, compares GitHub's digest when present, checks published size and UDIF format, runs `hdiutil verify`, and mounts read-only without opening Finder. It checks `Macventory.app`, its bundle identifier (`org.vadimtanel.Macventory`), executable, version, macOS 13.0 minimum, ARM64 architecture and code-signature integrity. Ad-hoc signature verification does not establish Developer ID or notarization. The mount is detached even when app checks fail.

The updater accepts only the reviewed Cask template. Only the version and checksum change, atomically, after artifact validation. Packaging or identity changes require a maintainer review and corresponding updater changes. The workflow also revalidates the current version's artifact, including its pinned checksum, on unchanged runs.

Before publication, every run executes mocked updater/publication tests, Ruby syntax, Homebrew Cask loading and URL/version/checksum consistency, online audit, and style checks. Any failure stops the workflow and appears under its named check in Actions. A failed validation never pushes the candidate; the published working Cask remains unchanged. Temporary runner files are discarded with the runner.

The separate `Validate Tap` workflow (`.github/workflows/validate.yml`) runs on pushes to `main`, pull requests and manual dispatch. It tests the updater and publisher, Ruby syntax, and the pinned Cask's Homebrew metadata, online audit and style. It has read-only repository permissions and never publishes. It does not run the updater or validate the latest release artifact, so regression tests and metadata/style checks can run while a new release is missing its assets. Homebrew's online audit independently discovers releases through livecheck and can still fail on a version mismatch until the new verified Cask is published. Style runs even after an audit failure; that failure still fails the job. No check is waived. A green result alone does not establish 1.1.0 installation or upgrade support.

`scripts/publish_cask.sh` allows only a changed `Casks/macventory.rb`, verifies the version, fetches remote main again, and refuses a stale checkout. A shared workflow concurrency group serializes runs; Git's normal fast-forward push is the final race guard. No force pushes or history rewriting are used. No-op runs do not commit. The message is `chore: update Macventory cask to v<version>`.

## Permissions and repository configuration

Only the update job requests `contents: write`; unspecified token permissions are disabled. Checkout is the official `actions/checkout`, pinned to the reviewed v7.0.1 commit (Node 24). The workflow uses the automatic same-repository `GITHUB_TOKEN`; no PAT or additional secret is required. API credentials are never passed to release-asset download URLs.

Repository settings inspected during setup: Actions enabled; default Workflow permissions set to **Read repository contents and packages permissions**; Actions PR creation disabled. Retain the read-only default: the workflow's explicit job permission requests the necessary scoped write access. There is no need to grant all workflows broad write permissions or enable PR creation for direct updates.

If a repository/organization policy denies the requested permission, an administrator must allow this updater's `contents: write` scope. Check **Settings → Actions → General → Workflow permissions** and any overriding organization policy; do not add a broad PAT as a workaround.

If branch protection/rulesets require PRs, direct publication will fail with GitHub's exact rejection in the push log. Keep protections enabled. Configure a reviewed PR publisher instead, granting that job `contents: write` and `pull-requests: write`, and enabling **Allow GitHub Actions to create and approve pull requests** if needed for PR creation. This implementation deliberately reports that configuration requirement instead of disabling protections or silently bypassing review.

A main-repository Release event does not trigger this separate Tap. An optional future cross-repository dispatch requires a narrowly scoped GitHub App token or fine-grained credential stored as a secret; the main repository's default token cannot write here. Scheduled/manual operation requires neither.

## Running and testing

In GitHub Actions select **Update Macventory Cask → Run workflow → main**. Scheduled execution may be delayed and can be disabled after 60 days of inactivity in a public repository; re-enable the workflow in Actions if necessary. No instantaneous synchronization is promised.

Local mocked tests (no network or application installation):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Read-only real-artifact inspection on macOS (Python 3.9+, curl, hdiutil, lipo, codesign):

```bash
python3 scripts/update_cask.py --verify-current
```

For a newer release this also prepares the verified Cask locally; it does not commit or push. The workflow performs the subsequent Homebrew checks before publishing. Review local changes before committing manually.

Tests cover initial/same-version no-ops, repeated execution, new stable releases, numeric comparison, prereleases/drafts, invalid tags, missing/duplicate/incomplete DMGs, wrong URLs, empty/oversized/truncated files, checksum mismatches, network/API failures, identity/version/architecture rejection, mount cleanup, unexpected Cask structure, replacement of an existing release's bytes, and concurrent publication against a temporary local bare remote. Future releases use fixtures, never fabricated GitHub Releases or tags.

Explicit fixtures cover transitions from 1.1.0 to 1.1.1, 1.2.0 and 2.0.0, a changed checksum on a subsequent release, refusal to downgrade, and the published 1.1.0 release with zero assets. Publication tests also simulate a server rejecting the push and a stale local checkout; neither may change remote main. The existing updater supports these versions without a version-specific code change.

## Missing or delayed uploads

Publishing GitHub release notes does not upload a DMG. The generated GitHub source-download links also do not replace the reviewed, named source archive. If the required DMG is absent, duplicated, empty, incomplete, or fails byte/app/signature validation, the updater exits unsuccessfully before changing the Cask. Later checks and publication do not run. Complete and verify the official release upload, then dispatch the updater on current `main`; do not edit the Cask to an unverified version or use `sha256 :no_check`.

The DMG is the updater's required installation asset. ZIP, checksum list and reviewed source archive are also required by the v1.1.0 application release checklist, but are not inputs to Homebrew installation. Missing them must be resolved as part of application release completion. Uploading application-release assets requires the owner's approval; a Tap update does not authorize that upload. The exact candidate provenance and proposed upload command are recorded in [RELEASE-1.1.0.md](RELEASE-1.1.0.md).

A real future-release bot commit can only be confirmed once a newer supported official release exists. A successful unchanged hosted run validates checks and the no-op path, not future-release publication permission.
