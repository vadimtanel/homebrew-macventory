#!/bin/bash
# Called only after all checks pass. Refuse stale checkouts and unrelated changes.
set -euo pipefail
version="${1:?Expected validated version}"
if [[ ! "$version" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
  echo 'Invalid publication version' >&2
  exit 1
fi
if [[ -z "$(git status --porcelain)" ]]; then
  echo 'No changes; no commit needed.'
  exit 0
fi
if [[ "$(git status --porcelain)" != ' M Casks/macventory.rb' ]]; then
  echo 'Refusing publication: working tree contains unexpected changes.' >&2
  exit 1
fi
if ! grep -Fxq "  version \"$version\"" Casks/macventory.rb; then
  echo 'Publication version does not match the validated Cask.' >&2
  exit 1
fi
git fetch --no-tags origin main
if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]]; then
  echo 'Remote main changed during validation; rerun the workflow on current main.' >&2
  exit 1
fi
git add -- Casks/macventory.rb
git -c user.name='github-actions[bot]' \
    -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
    commit -m "chore: update Macventory cask to v$version" -- Casks/macventory.rb
if ! git push origin HEAD:refs/heads/main; then
  echo 'Push failed. Check the error above for a concurrent update or branch protection.' >&2
  echo 'Keep protections enabled. If main requires PRs, configure a reviewed PR publisher with contents: write and pull-requests: write, and allow Actions to create PRs.' >&2
  exit 1
fi
