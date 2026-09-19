#!/bin/bash
# =============================================================================
# Setup GCP — Chatbot RAG Político
# Executa uma vez para provisionar toda a infraestrutura no GCP
# Pré-requisito: gcloud auth login + gcloud config set project rag-eleicoes
# =============================================================================

set -euo pipefail

PROJECT_ID="rag-eleicoes"
REGION="southamerica-east1"
REPO_NAME="chatbot-rag"
SERVICE_NAME="chatbot-rag-api"

echo "=== [1/6] Habilitando APIs ==="
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  firebasehosting.googleapis.com \
  --project="${PROJECT_ID}"

echo "=== [2/6] Criando Artifact Registry ==="
gcloud artifacts repositories describe "${REPO_NAME}" \
  --location="${REGION}" --project="${PROJECT_ID}" 2>/dev/null || \
gcloud artifacts repositories create "${REPO_NAME}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="Imagens Docker do chatbot RAG" \
  --project="${PROJECT_ID}"

echo "=== [3/6] Criando Secrets no Secret Manager ==="
# Para cada secret, só cria se não existir
for SECRET_NAME in PINECONE_API_KEY PINECONE_INDEX_NAME OPENROUTER_API_KEY HF_TOKEN GOOGLE_API_KEY; do
  if ! gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" 2>/dev/null; then
    echo "  → Criando secret: ${SECRET_NAME}"
    echo -n "PLACEHOLDER" | gcloud secrets create "${SECRET_NAME}" \
      --data-file=- \
      --replication-policy=automatic \
      --project="${PROJECT_ID}"
    echo "  ⚠️  Secret '${SECRET_NAME}' criado com valor PLACEHOLDER. Atualize com:"
    echo "     echo -n 'VALOR_REAL' | gcloud secrets versions add ${SECRET_NAME} --data-file=-"
  else
    echo "  ✓ Secret '${SECRET_NAME}' já existe"
  fi
done

echo "=== [4/6] Configurando IAM (Cloud Build → Cloud Run + Secrets) ==="
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

for ROLE in roles/run.admin roles/iam.serviceAccountUser roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${CB_SA}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet 2>/dev/null
done
echo "  ✓ IAM bindings configurados para Cloud Build"

echo "=== [5/6] Deploy inicial no Cloud Run (primeira vez) ==="
echo "  Building e fazendo push da imagem..."
gcloud builds submit \
  --tag="southamerica-east1-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/api:initial" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --quiet

echo "  Deploying no Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="southamerica-east1-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/api:initial" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=3 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-secrets="PINECONE_API_KEY=PINECONE_API_KEY:latest,PINECONE_INDEX_NAME=PINECONE_INDEX_NAME:latest,OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest,HF_TOKEN=HF_TOKEN:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest" \
  --port=10000 \
  --project="${PROJECT_ID}" \
  --quiet

CLOUD_RUN_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" --project="${PROJECT_ID}" \
  --format='value(status.url)')

echo "  ✓ Cloud Run deployed: ${CLOUD_RUN_URL}"

echo "=== [6/6] Deploy frontend no Firebase Hosting ==="
echo "  Building frontend..."
cd frontend
npm ci
VITE_API_URL="${CLOUD_RUN_URL}" npm run build
cd ..

echo "  Deploying Firebase Hosting..."
firebase deploy --only hosting --project="${PROJECT_ID}" --non-interactive

echo ""
echo "============================================="
echo "  ✅ Migração GCP concluída!"
echo "  API:      ${CLOUD_RUN_URL}"
echo "  Frontend: https://${PROJECT_ID}.web.app"
echo "============================================="
echo ""
echo "⚠️  Próximos passos manuais:"
echo "  1. Atualize os secrets com valores reais (se criou com PLACEHOLDER)"
echo "  2. Crie o Cloud Build trigger no console:"
echo "     https://console.cloud.google.com/cloud-build/triggers?project=${PROJECT_ID}"
echo "  3. Atualize VITE_API_URL no cloudbuild.yaml com: ${CLOUD_RUN_URL}"
echo "  4. Rotacione a private key do service account (foi exposta no chat)"
