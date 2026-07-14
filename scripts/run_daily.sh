#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Uses public GET-only ATS endpoints. No automatic applications.
./scripts/job-radar \
  --profile config/profile.toml \
  --sources config/sources.toml \
  run --allow-network
