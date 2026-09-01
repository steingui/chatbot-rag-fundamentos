#!/bin/bash
# Helper script to fetch backend Cloud Run logs for the last X minutes

MINUTES=${1:-30}
SERVICE_NAME=${2:-"chatbot-rag-api"}
PROJECT_ID=${3:-"rag-eleicoes"}

# Determine gcloud executable
GCLOUD_BIN="gcloud"
if [ -f "/tmp/google-cloud-sdk/bin/gcloud" ]; then
    GCLOUD_BIN="/tmp/google-cloud-sdk/bin/gcloud"
fi

SINCE=$(date -u -d "$MINUTES minutes ago" +"%Y-%m-%dT%H:%M:%SZ")

echo "=== Consultando logs do Cloud Run ($SERVICE_NAME) nos últimos $MINUTES minutos ==="
$GCLOUD_BIN logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND timestamp >= \"$SINCE\"" \
    --project="$PROJECT_ID" \
    --limit=100 \
    --format="value(timestamp,severity,textPayload,jsonPayload.message)"
