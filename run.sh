#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "$EUID" -eq 0 ]]; then
  echo 'Run as your normal user, not root.' >&2
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  bash install.sh --dashboard-only
fi
export PATH="$HOME/.local/bin:$HOME/go/bin:/usr/local/go/bin:$PATH"
if [[ "$(uname -s)" == Darwin ]]; then
  case "$(uname -m)" in
    arm64) export PATH="$HOME/.local/bin:/opt/homebrew/bin:/opt/homebrew/sbin:$PATH" ;;
    x86_64) export PATH="$HOME/.local/bin:/usr/local/bin:/usr/local/sbin:$PATH" ;;
  esac
fi
umask 077
skip_tools=false
for option in "$@"; do
  [[ "$option" != --no-tool-setup ]] || skip_tools=true
done
extra=()
# WSL/headless package-manager prompts stay in this terminal.
if [[ "$(uname -s)" == Linux && "$skip_tools" == false ]] && { [[ -n "${WSL_DISTRO_NAME:-}${WSL_INTEROP:-}" ]] || [[ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; }; then
  if ! .venv/bin/python setup_tools.py --install; then
    echo 'Some backends need attention. Read the installer output and use Tool health / Setup all tools to retry.' >&2
  fi
  extra+=(--no-tool-setup)
fi
exec .venv/bin/python app.py "${extra[@]}" "$@"
