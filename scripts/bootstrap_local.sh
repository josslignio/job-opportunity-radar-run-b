#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python3 -m unittest discover -s tests -v
rm -rf .demo-runtime
python3 -m job_radar \
  --profile config/profile.toml \
  --sources tests/fixtures/sources.toml \
  --runtime-root .demo-runtime \
  run --fixture-dir tests/fixtures

printf '\nDemo report: %s\n' "$ROOT/.demo-runtime/runs/latest/report.html"
