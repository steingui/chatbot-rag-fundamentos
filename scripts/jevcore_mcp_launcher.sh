#!/usr/bin/env bash
# Lançador do jevcore-mcp para o Roo Code.
# Lê as credenciais do .env do projeto (gitignored) e executa o bin global.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$DIR/../.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ENV_FILE"
  set +a
fi

export JEV_PROVIDER="${JEV_PROVIDER:-openrouter}"
export OPENROUTER_MODEL="${OPENROUTER_MODEL:-typesafe/jev-1.13}"

exec node /home/gui/.npm-global/lib/node_modules/jevcore-mcp/lib/bin.js
