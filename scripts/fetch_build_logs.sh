#!/bin/bash
# =============================================================================
# Busca logs de build do Cloud Build (deploy completo: backend + frontend)
# dos últimos N minutos, ancorados no último build.
# Uso: ./scripts/fetch_build_logs.sh [MINUTOS]
# =============================================================================

MINUTES=${1:-30}
PROJECT_ID=${2:-"rag-eleicoes"}

# Resolve o binário do gcloud
GCLOUD_BIN="$(command -v gcloud 2>/dev/null || true)"
if [ -z "$GCLOUD_BIN" ]; then
  if [ -x "/home/gui/google-cloud-sdk/bin/gcloud" ]; then
    GCLOUD_BIN="/home/gui/google-cloud-sdk/bin/gcloud"
  else
    echo "ERRO: gcloud não encontrado no PATH nem em /home/gui/google-cloud-sdk." >&2
    exit 1
  fi
fi

# Último build
LAST_LINE="$("$GCLOUD_BIN" builds list \
  --project="$PROJECT_ID" \
  --format="value(createTime,id,status)" \
  --limit=1 2>/dev/null | head -1)"

LAST_TS="$(echo "$LAST_LINE" | cut -f1 | sed 's/\.[0-9]*Z$/Z/; s/+00:00$//')"
LAST_ID="$(echo "$LAST_LINE" | cut -f2)"
LAST_STATUS="$(echo "$LAST_LINE" | cut -f3)"

WINDOW_START="$(date -u -d "$MINUTES minutes ago" +"%Y-%m-%dT%H:%M:%SZ")"

# Janela efetiva: cobre no mínimo desde o último build; senão os últimos N minutos.
if [ -n "$LAST_TS" ] && [ "$LAST_TS" \< "$WINDOW_START" ]; then
  SINCE="$WINDOW_START"
else
  SINCE="${LAST_TS:-$WINDOW_START}"
fi

echo "=== Último build: ${LAST_ID:-desconhecido} (${LAST_TS:-n/d}, ${LAST_STATUS:-n/d}) ==="
echo "=== Logs do Cloud Build desde $SINCE (janela de $MINUTES min) ==="

"$GCLOUD_BIN" logging read \
  "resource.type=build AND timestamp >= \"$SINCE\"" \
  --project="$PROJECT_ID" \
  --limit=200 \
  --order=asc \
  --format="value(timestamp,severity,textPayload)"
