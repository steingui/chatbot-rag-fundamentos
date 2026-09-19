---
name: logs-backend
description: Busca logs de produção do backend (Cloud Run) dos últimos N minutos (default 30), ancorados no último deploy.
---

# Logs do Backend (Cloud Run)

## Instructions

1. Extraia o número de minutos do argumento da invocação (ex.: `@logs-backend 10` → `10`). Se ausente, use `30`.
2. Execute:
   ```bash
   ./scripts/fetch_deploy_logs.sh <MINUTOS>
   ```
3. Analise a saída e destaque anomalias:
   - `severity` `ERROR`/`CRITICAL` ou `WARNING` com mensagem relevante.
   - Requisições HTTP com status >= 400 (`404`, `405`, `500`, etc.).
   - Tracebacks, timeouts ou reinícios por crash (não `DEPLOYMENT_ROLLOUT`).
4. Resuma em bullets: timestamp, severidade, rota/endpoint e causa provável. Sem anomalias → reporte pipeline saudável.
