#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/dist}"
command -v dpkg-deb >/dev/null || { echo 'dpkg-deb is required to build the package.' >&2; exit 1; }
mkdir -p -- "$OUT"
WORK="$(mktemp -d)"
trap 'rm -rf -- "$WORK"' EXIT
VERSION="$(cd -- "$ROOT" && python3 -c 'from echo_recon import __version__; print(__version__)')"
COMMIT_EPOCH="$(git -C "$ROOT" log -1 --format=%ct 2>/dev/null || true)"
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-${COMMIT_EPOCH:-0}}"
[[ "$VERSION" =~ ^[0-9]+([.][0-9]+)*([+~.-][A-Za-z0-9.+~:-]+)?$ ]] || { echo "Invalid Debian package version: $VERSION" >&2; exit 1; }
if [[ -n "${GITHUB_REF_NAME:-}" && "$GITHUB_REF_NAME" != "v$VERSION" ]]; then
  echo "Release tag $GITHUB_REF_NAME must match application version v$VERSION." >&2
  exit 1
fi

PACKAGE="$WORK/echo-recon"
install -d -m 0755 "$PACKAGE/DEBIAN" "$PACKAGE/usr/lib/echo-recon" \
  "$PACKAGE/usr/bin" "$PACKAGE/usr/share/applications" "$PACKAGE/usr/share/doc/echo-recon"
sed "s/@VERSION@/$VERSION/" "$ROOT/packaging/debian/control.in" > "$PACKAGE/DEBIAN/control"
cp "$ROOT/app.py" "$ROOT/setup_tools.py" "$ROOT/setup_tools_windows.py" "$ROOT/doctor.py" "$PACKAGE/usr/lib/echo-recon/"
cp -a "$ROOT/echo_recon" "$ROOT/static" "$ROOT/templates" "$PACKAGE/usr/lib/echo-recon/"
find "$PACKAGE/usr/lib/echo-recon" -type d -name __pycache__ -prune -exec rm -rf -- {} +
find "$PACKAGE/usr/lib/echo-recon" -type f -name '*.py[co]' -delete
install -m 0755 "$ROOT/packaging/debian/echo-recon" "$PACKAGE/usr/bin/echo-recon"
install -m 0644 "$ROOT/packaging/debian/echo-recon.desktop" "$PACKAGE/usr/share/applications/echo-recon.desktop"
install -m 0644 "$ROOT/LICENSE" "$ROOT/NOTICE.md" "$PACKAGE/usr/share/doc/echo-recon/"
chmod -R u=rwX,go=rX "$PACKAGE/usr/lib/echo-recon"

ARCHIVE="$OUT/echo-recon_${VERSION}_all.deb"
dpkg-deb --build --root-owner-group "$PACKAGE" "$ARCHIVE"
dpkg-deb --info "$ARCHIVE"
echo "Built $ARCHIVE"
