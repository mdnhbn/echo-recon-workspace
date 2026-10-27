#!/usr/bin/env bash
# Refuse release rollback before changing the published pool or metadata.
set -euo pipefail

VERSION="${1:?Usage: check-feed-version.sh VERSION POOL_DIRECTORY}"
POOL="${2:?Usage: check-feed-version.sh VERSION POOL_DIRECTORY}"
[[ "$VERSION" =~ ^[0-9]+([.][0-9]+)*([+~.-][A-Za-z0-9.+~:-]+)?$ ]] || { echo 'Invalid incoming Debian version.' >&2; exit 1; }
command -v dpkg-deb >/dev/null || { echo 'dpkg-deb is required.' >&2; exit 1; }
command -v dpkg >/dev/null || { echo 'dpkg is required.' >&2; exit 1; }

shopt -s nullglob
for package in "$POOL"/echo-recon_*.deb; do
  published="$(dpkg-deb --field "$package" Version)"
  if dpkg --compare-versions "$VERSION" lt "$published"; then
    echo "Refusing to replace published Echo Recon $published with older version $VERSION." >&2
    exit 1
  fi
done
