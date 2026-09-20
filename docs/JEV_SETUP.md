# Jev (TypeSafe) — Integração via OpenRouter + jevcore-mcp

## O que é o Jev

O **Jev** é o modelo de decisão estruturada da [TypeSafe](https://typesafe.ai/). Em vez de
gerar texto livre, ele responde a **perguntas tipadas** sobre um estado, retornando respostas
determinísticas e estruturadas:

- `Noul` — probabilidade (0–1) de uma instrução ser verdadeira.
- `Choice` — escolha entre critérios predefinidos.
- `Score` — nota numérica segundo critérios.

## Estado atual (destravado ✅)

O Jev está **funcionando de verdade** via OpenRouter. A cadeia validada ponta a ponta:

```
agente → .mcp.json → scripts/jevcore_mcp_launcher.sh → node (bin global) → jevcore-mcp
       → OpenRouterProvider → POST https://openrouter.ai/api/v1/systemone → TypeSafe Jev
```

Resposta real observada (sem `SYNTHETIC`, sem mock):

```json
{
  "provider": "openrouter",
  "model": "typesafe/jev-1.13-20260917",
  "answers": { "util": { "type": "noul", "noul": 0.19 } },
  "usage": { "inputTokens": 293, "outputTokens": 21 }
}
```

Custo por chamada `jev_ask` (1 pergunta noul): ~`0.000012` USD.

## Credenciais

| Variável | Estado |
|----------|--------|
| `OPENROUTER_API_KEY` | Definida com chave real em [`.env`](../.env) (gitignored) |
| `OPENROUTER_MODEL` | `typesafe/jev-1.13` (padrão do launcher) |
| `AI_GATEWAY_API_KEY` | Obsoleta — Vercel AI Gateway **não** expõe `/v1/systemone` |
| `TYPESAFE_API_KEY` | Ausente (fora da whitelist) — não necessária neste caminho |

> Detalhe importante: o modelo default do SDK é `jev-latest`, que **não resolve** no
> OpenRouter (`404`). O id válido é `typesafe/jev-1.13` (o provider retorna a variante
> datada `typesafe/jev-1.13-20260917`). O launcher já fixa o id correto.

## Como está instalado

- Pacote global: `npm install -g jevcore-mcp --prefix /home/gui/.npm-global`.
- O bin `jevcore-mcp` do pacote **não tem shebang** (npm o publica sem `#!/usr/bin/env node`),
  então `npx -y jevcore-mcp` falha com `Permission denied`. Por isso o registro no
  [`.mcp.json`](../.mcp.json) chama `node` direto no `lib/bin.js`, via
  [`scripts/jevcore_mcp_launcher.sh`](../scripts/jevcore_mcp_launcher.sh).

## Registro MCP

[`.mcp.json`](../.mcp.json):

```json
"jevcore": {
  "command": "bash",
  "args": ["/home/gui/Área de trabalho/repositories/chatbot-rag-fundamentos/scripts/jevcore_mcp_launcher.sh"]
}
```

O launcher lê o `.env` do projeto (fallback para env do host), fixa
`JEV_PROVIDER=openrouter` e `OPENROUTER_MODEL=typesafe/jev-1.13`, e executa o bin global.

## Ferramentas expostas

- `jev_ask` — perguntas tipadas (`noul`, `choice`, `score`) sobre um estado.
- `jev_rank` — ranqueia candidatos por relevância (`noul` por candidato).
- `jev_check` — verifica se uma evidência suporta/contradiz/é suficiente para uma afirmação.

## Teste manual

```bash
OPENROUTER_API_KEY="sk-or-v1-..." OPENROUTER_MODEL="typesafe/jev-1.13" \
  node /home/gui/.npm-global/lib/node_modules/jevcore-mcp/lib/bin.js
```

Ou, para validar a rota diretamente:

```bash
curl -sS -X POST "https://openrouter.ai/api/v1/systemone" \
  -H "Authorization: Bearer sk-or-v1-..." \
  -H "Content-Type: application/json" \
  -d '{"state":{"context":"teste"},"model":"typesafe/jev-1.13",
       "questions":{"q1":{"type":"noul","instructions":"O contexto é útil?"}}}'
```

## Por que não Vercel AI Gateway

A Vercel AI Gateway lista `typesafe-ai/jev` no catálogo, mas só fala o protocolo
OpenAI-compatible (`/v1/chat/completions`, `/v1/responses`). O endpoint próprio da
TypeSafe (`/v1/systemone`) não existe lá — `404`. A ponte local
[`scripts/jev_bridge.py`](../scripts/jev_bridge.py) permanece no repo como referência,
mas não é o caminho ativo.

## Doc oficial

- https://typesafe.ai/docs
- https://openrouter.ai/docs/guides/community/typesafe-sdk
- https://www.npmjs.com/package/jevcore-mcp
