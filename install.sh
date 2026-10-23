#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "$EUID" -eq 0 ]]; then
  echo 'Use your normal account. Do not run this installer with sudo.' >&2
  exit 1
fi
umask 077
command -v python3 >/dev/null || { echo 'Install python3 and python3-venv first.'; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements.txt
echo 'Dashboard installed. Run: bash run.sh'
echo 'The eight optional assessment tools are managed separately; see docs/TOOLS.md.'
