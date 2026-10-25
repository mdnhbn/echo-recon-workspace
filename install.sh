#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
dashboard_only=false
for option in "$@"; do
  case "$option" in
    --dashboard-only) dashboard_only=true ;;
    *) echo "Unknown option: $option (supported: --dashboard-only)" >&2; exit 2 ;;
  esac
done
if [[ "$EUID" -eq 0 ]]; then
  echo 'Use your normal account. Do not run this installer with sudo.' >&2
  exit 1
fi
umask 077
task_python=python3
setup_script=setup_tools.py
if [[ "$(uname -s)" == Darwin ]]; then
  mac_arch="$(uname -m)"
  if [[ "$(/usr/sbin/sysctl -in sysctl.proc_translated 2>/dev/null || true)" == 1 ]]; then
    echo 'Use native macOS Terminal and Homebrew, without Rosetta. See docs/MACOS.md.' >&2
    exit 1
  fi
  case "$mac_arch" in
    arm64) brew_prefix=/opt/homebrew ;;
    x86_64) brew_prefix=/usr/local ;;
    *) echo 'macOS setup requires native Apple Silicon or Intel. See docs/MACOS.md.' >&2; exit 1 ;;
  esac
  export PATH="$HOME/.local/bin:$brew_prefix/bin:$brew_prefix/sbin:$PATH"
  task_python=
  for candidate in "$brew_prefix/opt/python@3.12/bin/python3.12" "$brew_prefix/bin/python3.12" "$brew_prefix/bin/python3" python3; do
    if command -v "$candidate" >/dev/null && "$candidate" -c 'import platform,sys; sys.exit(0 if sys.version_info >= (3,12) and platform.machine() == sys.argv[1] else 1)' "$mac_arch" 2>/dev/null; then
      task_python="$candidate"
      break
    fi
  done
  [[ -n "$task_python" ]] || { echo 'Install native Homebrew and run: brew install python@3.12 git (see docs/MACOS.md).' >&2; exit 1; }
  setup_script=setup_tools_macos.py
else
  command -v "$task_python" >/dev/null || { echo 'Install Python 3.12+ and its venv package first.' >&2; exit 1; }
  "$task_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' || { echo 'The dashboard requires Python 3.11+; portable backends require Python 3.12+.' >&2; exit 1; }
fi
if [[ -e .venv ]]; then
  if [[ ! -x .venv/bin/python ]]; then
    echo 'Existing .venv is unrecognized and was preserved. Install in a fresh project folder.' >&2
    exit 1
  fi
  selected_version="$("$task_python" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  existing_version="$(.venv/bin/python -c 'import sys; print("%d.%d" % sys.version_info[:2])')" || { echo 'Existing .venv is broken and was preserved. Use a fresh project folder.' >&2; exit 1; }
  if [[ "$selected_version" != "$existing_version" ]]; then
    echo 'Existing .venv uses a different Python version and was preserved. Use a fresh project folder; keep a private backup of data.' >&2
    exit 1
  fi
  if [[ "$setup_script" == setup_tools_macos.py ]]; then
    existing_arch="$(.venv/bin/python -c 'import platform; print(platform.machine())')" || { echo 'Existing .venv is broken and was preserved. Use a fresh project folder.' >&2; exit 1; }
    if [[ "$existing_arch" != "$mac_arch" ]]; then
      echo 'Existing .venv uses a different Mac processor architecture and was preserved. Use a fresh project folder with native Python; keep a private backup of data.' >&2
      exit 1
    fi
  fi
fi
"$task_python" -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements.txt
export PATH="$HOME/.local/bin:$HOME/go/bin:/usr/local/go/bin:$PATH"
if [[ "$dashboard_only" == false ]]; then
  .venv/bin/python "$setup_script" --install
fi
echo 'Dashboard installed. Run: bash run.sh'
echo 'First startup checks missing backends; Setup all tools retries their fixed installer.'
