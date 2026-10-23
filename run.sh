#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "$EUID" -eq 0 ]]; then
  echo 'Run as your normal user, not root.' >&2
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  echo 'First run: bash install.sh' >&2
  exit 1
fi
export PATH="$HOME/.local/bin:$HOME/go/bin:/usr/local/go/bin:$PATH"
umask 077
exec .venv/bin/python app.py
