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
command -v python3 >/dev/null || { echo 'Install Python 3.12+ and its venv package first.' >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' || { echo 'The dashboard requires Python 3.11+; portable backends require Python 3.12+.' >&2; exit 1; }
if [[ -e .venv ]]; then
  if [[ ! -x .venv/bin/python ]]; then
    echo 'Existing .venv is unrecognized and was preserved. Install in a fresh project folder.' >&2
    exit 1
  fi
  selected_version="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  existing_version="$(.venv/bin/python -c 'import sys; print("%d.%d" % sys.version_info[:2])')" || { echo 'Existing .venv is broken and was preserved. Use a fresh project folder.' >&2; exit 1; }
  if [[ "$selected_version" != "$existing_version" ]]; then
    echo 'Existing .venv uses a different Python version and was preserved. Use a fresh project folder; keep a private backup of data.' >&2
    exit 1
  fi
fi
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements.txt
export PATH="$HOME/.local/bin:$HOME/go/bin:/usr/local/go/bin:$PATH"
if [[ "$dashboard_only" == false ]]; then
  .venv/bin/python setup_tools.py --install
fi
echo 'Dashboard installed. Run: bash run.sh'
echo 'First startup checks missing backends; Setup all tools retries their fixed installer.'
