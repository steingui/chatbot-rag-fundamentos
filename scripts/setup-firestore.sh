#!/bin/bash
# =============================================================================
# Setup Firestore — Chatbot RAG Político (INF-403)
# Cria o banco Firestore NoSQL em southamerica-east1 (São Paulo) e aplica
# regras de acesso + índices declarativos via Firebase CLI.
# Pré-requisito: gcloud auth login + firebase login (ou token FIREBASE_TOKEN)
# =============================================================================

set -euo pipefail

PROJECT_ID="${1:-rag-eleicoes}"

echo "=== [1/3] Criando banco Firestore em southamerica-east1 ==="
gcloud firestore databases create \
  --project="${PROJECT_ID}" \
  --location=southamerica-east1 \
  --type=firestore-native

echo "=== [2/3] Implantando regras de acesso (firestore.rules) ==="
firebase deploy --only firestore:rules --project="${PROJECT_ID}" --non-interactive

echo "=== [3/3] Implantando índices (firestore.indexes.json) ==="
firebase deploy --only firestore:indexes --project="${PROJECT_ID}" --non-interactive

echo ""
echo "============================================="
echo "  ✅ Firestore configurado em southamerica-east1 (${PROJECT_ID})"
echo "============================================="
