#!/usr/bin/env bash
# Restart local Prompt Studio (stop port listeners, then start foreground).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x ./.venv/bin/python ]]; then
  exec ./.venv/bin/python -m apps.prompt_studio restart "$@"
fi
exec python -m apps.prompt_studio restart "$@"
