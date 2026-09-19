#!/usr/bin/env bash
# INF-402: Sincroniza variáveis de ambiente locais (.env) com o GCP Secret Manager.
# Idempotente: cria secret ausente; só adiciona versão nova se o valor mudar.
# Uso: ./scripts/sync_secrets.sh [.env]
set -euo pipefail

ENV_FILE="${1:-.env}"
PROJECT_ID="${GCP_PROJECT_ID:-rag-eleicoes}"

# secret (Secret Manager) => variável correspondente no .env local
declare -A SECRET_FROM_ENV=(
  [OPENROUTER_API_KEY]=OPENROUTER_API_KEY
  [PINECONE_API_KEY]=PINECONE_API_KEY
  [PINECONE_INDEX_NAME]=PINECONE_INDEX_NAME
  [HF_TOKEN]=HF_TOKEN
  [GOOGLE_API_KEY]=MEU_GOOGLE_API_KEY
  [GEMINI_API_KEY]=MEU_GEMINI_API_KEY
)

# Carrega o .env sem expor valores no log
declare -A ENV_VALUES
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  key="${line%%=*}"
  value="${line#*=}"
  key="${key//[[:space:]]/}"
  value="${value#\"}"; value="${value%\"}"
  value="${value#\'}"; value="${value%\'}"
  ENV_VALUES["$key"]="$value"
done < "$ENV_FILE"

for secret in "${!SECRET_FROM_ENV[@]}"; do
  env_var="${SECRET_FROM_ENV[$secret]}"
  local_value="${ENV_VALUES[$env_var]:-}"

  if [[ -z "$local_value" ]]; then
    echo "SKIP   $secret (var '$env_var' ausente em $ENV_FILE)"
    continue
  fi

  if ! gcloud secrets describe "$secret" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "CREATE $secret"
    printf '%s' "$local_value" | gcloud secrets create "$secret" \
      --project="$PROJECT_ID" \
      --data-file=- \
      --replication-policy=automatic
    continue
  fi

  current="$(gcloud secrets versions access latest --secret="$secret" --project="$PROJECT_ID" 2>/dev/null || true)"
  if [[ "$current" == "$local_value" ]]; then
    echo "OK     $secret (sem mudança)"
  else
    echo "UPDATE $secret"
    printf '%s' "$local_value" | gcloud secrets versions add "$secret" \
      --project="$PROJECT_ID" \
      --data-file=-
  fi
done

echo "Sync concluído para o projeto: $PROJECT_ID"
