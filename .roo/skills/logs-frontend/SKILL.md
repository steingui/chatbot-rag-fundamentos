---
name: logs-frontend
description: Busca logs de build/deploy do frontend (Cloud Build → Firebase Hosting) dos últimos N minutos (default 30), ancorados no último build.
---

# Logs do Frontend (Cloud Build → Firebase Hosting)

## Contexto

O Firebase Hosting não emite logs de request para o Cloud Logging por padrão. O
observável mais próximo é o build do frontend no Cloud Build (passo `npm run
build` + `firebase deploy --only hosting` do `cloudbuild.yaml`).

## Instructions

1. Extraia o número de minutos do argumento da invocação (ex.: `@logs-frontend 10` → `10`). Se ausente, use `30`.
2. Execute:
   ```bash
   ./scripts/fetch_build_logs.sh <MINUTOS>
   ```
3. Analise a saída e destaque anomalias:
   - `Step #3` (build npm) ou `Step #4` (deploy firebase) com erro ou falha.
   - Status do último build diferente de `SUCCESS`.
   - Erros de `tsc`/`vite` ou falha no `firebase deploy`.
4. Resuma em bullets: build id, status, passo com falha e causa provável. Sem anomalias → reporte build saudável.
