#!/bin/bash
# =============================================================================
# Busca logs de produção do Cloud Run dos últimos N minutos, ancorados no
# último deploy: a janela nunca começa antes da revisão ready mais recente.
# Uso: ./scripts/fetch_deploy_logs.sh [MINUTOS]
# =============================================================================

MINUTES=${1:-30}
SERVICE_NAME=${2:-"chatbot-rag-api"}
PROJECT_ID=${3:-"rag-eleicoes"}
REGION=${4:-"southamerica-east1"}

# Resolve o binário do gcloud (PATH primeiro, depois instalação local)
GCLOUD_BIN="$(command -v gcloud 2>/dev/null || true)"
if [ -z "$GCLOUD_BIN" ]; then
  if [ -x "/home/gui/google-cloud-sdk/bin/gcloud" ]; then
    GCLOUD_BIN="/home/gui/google-cloud-sdk/bin/gcloud"
  else
    echo "ERRO: gcloud não encontrado no PATH nem em /home/gui/google-cloud-sdk." >&2
    exit 1
  fi
fi

# Última revisão pronta (timestamp de criação + nome)
LAST_LINE="$("$GCLOUD_BIN" run revisions list \
  --service="$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(metadata.creationTimestamp,metadata.name)" \
  --sort-by="~metadata.creationTimestamp" \
  --limit=1 2>/dev/null | head -1)"

LAST_TS="$(echo "$LAST_LINE" | cut -f1 | sed 's/\.[0-9]*Z$/Z/')"
LAST_NAME="$(echo "$LAST_LINE" | cut -f2)"

NOW="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
WINDOW_START="$(date -u -d "$MINUTES minutes ago" +"%Y-%m-%dT%H:%M:%SZ")"

# Janela efetiva: cobre no mínimo desde o último deploy; senão os últimos N minutos.
if [ -n "$LAST_TS" ] && [ "$LAST_TS" \< "$WINDOW_START" ]; then
  SINCE="$WINDOW_START"
else
  SINCE="${LAST_TS:-$WINDOW_START}"
fi

echo "=== Último deploy: ${LAST_NAME:-desconhecido} (${LAST_TS:-n/d}) ==="
echo "=== Logs do Cloud Run ($SERVICE_NAME) desde $SINCE (janela de $MINUTES min) ==="

"$GCLOUD_BIN" logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND timestamp >= \"$SINCE\"" \
  --project="$PROJECT_ID" \
  --limit=200 \
  --order=asc \
  --format="value(timestamp,severity,textPayload,jsonPayload.message)"
