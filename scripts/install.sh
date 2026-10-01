#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

if command -v uv >/dev/null 2>&1; then
  uv venv .venv
  uv pip install --python .venv/bin/python --no-cache "mcp<2" httpx pyyaml
else
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install "mcp<2" httpx pyyaml
fi

echo "Install complete."
echo "Next:"
echo "  1. copy config.example.yaml to config.yaml"
echo "  2. fill config/targets.yaml"
echo "  3. register dsh/recon-hub.yml"
echo "  4. run scripts/run-recon-hub.ps1"