# Jev — Alerting de Falhas

> Como detectar **automaticamente** falhas nas chamadas Jev no backend
> (Cloud Run + Cloud Logging + Cloud Monitoring).
>
> Backend: [`cloudbuild.yaml`](cloudbuild.yaml:25) implanta `chatbot-rag-api` no
> Cloud Run com `--set-secrets=...OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest...`
> e logging `CLOUD_LOGGING_ONLY` ([`cloudbuild.yaml`](cloudbuild.yaml:64)).

---

## 1. Contrato de log estruturado

Toda chamada em [`backend/rag/jev_client.py`](backend/rag/jev_client.py) deve
emitir **um** log JSON com o campo `event="jev_call"`:

```json
{
  "event": "jev_call",
  "routine": "r2_web_gate",
  "model": "typesafe/jev-1.13",
  "status": "ok | error | timeout | rate_limited | no_credits | low_confidence",
  "latency_ms": 342,
  "error": "mensagem curta (só em falha)"
}
```

Classificação de `status` por código HTTP do OpenRouter:

| Código | `status` | Severidade log |
|--------|----------|----------------|
| 200 | `ok` | INFO |
| 401 | `error` (chave inválida) | ERROR |
| 402 | `no_credits` (crédito esgotado) | ERROR |
| 429 | `rate_limited` | WARNING |
| 5xx / timeout | `error` / `timeout` | ERROR |
| circuit breaker aberto | `error` | WARNING |

**Regra de ouro:** falha Jev ⇒ fallback da rotina + log ERROR, **nunca**
exceção não tratada para o usuário.

**Guardrail de 90%:** quando `confidence < 0.9`, a rotina **não** usa a escolha
do Jev e delega às nossas LLMs (decider). Logar `status="low_confidence"` nesse
caso para rastrear a taxa de delegação (não é falha — é o guardrail operando).

---

## 2. Métrica baseada em log (Cloud Monitoring)

Criar uma **log-based metric** que conta chamadas Jev com falha (status ≠ ok):

```bash
gcloud logging metrics create jev_call_failures \
  --project=rag-eleicoes \
  --description="Chamadas Jev (OpenRouter System One) com status diferente de ok" \
  --log-filter='jsonPayload.event="jev_call" AND jsonPayload.status!="ok"'
```

Métricas complementares (opcionais, para dashboards):

```bash
gcloud logging metrics create jev_call_total \
  --project=rag-eleicoes \
  --log-filter='jsonPayload.event="jev_call"'

gcloud logging metrics create jev_no_credits \
  --project=rag-eleicoes \
  --log-filter='jsonPayload.event="jev_call" AND jsonPayload.status="no_credits"'
```

---

## 3. Política de alerta

Alerta quando a taxa de falha passar de **20%** (ou ≥ 10 falhas) em 5 minutos:

```bash
gcloud alpha monitoring policies create \
  --project=rag-eleicoes \
  --policy-from-file=docs/jev_alert_policy.json
```

Conteúdo de `docs/jev_alert_policy.json` (política com duas condições:
threshold de contagem e threshold de razão):

```json
{
  "displayName": "Jev falhando acima do limite",
  "conditions": [
    {
      "displayName": "Falhas Jev > 10 em 5min",
      "conditionThreshold": {
        "filter": "metric.type=\"logging.googleapis.com/user/jev_call_failures\" AND resource.type=\"cloud_run_revision\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 10,
        "duration": "300s",
        "trigger": { "count": 1 }
      }
    }
  ],
  "notificationChannels": ["projects/rag-eleicoes/notificationChannels/SEU_CANAL_AQUI"],
  "combiner": "OR"
}
```

> Nota: substituir `SEU_CANAL_AQUI` pelo canal de notificação (e-mail/Slack)
> criado em Cloud Monitoring → Alerting → Notification channels.

Sem canal de notificação configurado, ao menos o incidente fica visível em
Cloud Monitoring → Alerting (política aberta).

---

## 4. Alertas específicos por causa

| Falha | Ação recomendada |
|-------|------------------|
| `no_credits` (402) | Recarregar crédito OpenRouter; enquanto isso o fallback mantém o pipeline de pé |
| `error` 401 | Rotacionar `OPENROUTER_API_KEY` no Secret Manager e re-deploy |
| `rate_limited` (429) | Aumentar backoff no retry do `jev_client` |
| `timeout`/5xx | Verificar status do OpenRouter; circuit breaker já mitiga |

---

## 5. Consulta manual de falhas

Analógico a [`scripts/fetch_logs.sh`](scripts/fetch_logs.sh:1) — a criar em code
mode como `scripts/fetch_jev_errors.sh`:

```bash
gcloud logging read \
  'resource.type=cloud_run_revision AND resource.labels.service_name=chatbot-rag-api AND jsonPayload.event="jev_call" AND jsonPayload.status!="ok"' \
  --project=rag-eleicoes --limit=50 \
  --format="value(timestamp,jsonPayload.routine,jsonPayload.status,jsonPayload.error)"
```

Enquanto o script não existe, o comando acima roda direto no terminal.

---

## 6. Verificação pós-deploy (aceite do alerting)

1. Deploy do MVP (R1+R2).
2. Forçar falha: remover `OPENROUTER_API_KEY` do Secret por 1 minuto ou apontar
   `JEV_ENDPOINT` para URL inválida em staging.
3. Confirmar: logs `event="jev_call", status="error"` aparecem e a resposta ao
   usuário **continua normal** (fallback).
4. Confirmar: métrica `logging.googleapis.com/user/jev_call_failures` sobe e a
   política de alerta dispara.
