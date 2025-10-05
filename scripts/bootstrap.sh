#!/usr/bin/env bash
set -euo pipefail

mkdir -p var secrets

if [ ! -f secrets/master.key ]; then
  openssl rand -hex 32 > secrets/master.key
  echo "Generated secrets/master.key"
fi

echo "Bootstrap complete."
