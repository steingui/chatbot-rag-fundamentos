---
name: gcp-bug-fixer
description: Busca o grupo de erro mais crítico no GCP Error Reporting, tria o stack trace com gate Jev (código vs infra), implementa a correção em uma branch, valida com testes e abre um Pull Request com evidências.
---

# GCP Bug Fixer

## When to use
Use esta skill quando o usuário pedir para:
- "corrigir um erro do GCP"
- "resolver um bug de produção"
- "consertar o erro mais crítico do Error Reporting"
- ou digitar /fix-gcp-bug

## Prerequisites
- O MCP `gcp-observability` deve estar configurado com acesso à API Error Reporting.
- O MCP `github` deve estar configurado com um token com escopo `repo`.
- O MCP `playwright` deve estar configurado.
- O MCP `jevcore` deve estar configurado (gate de triagem).
- Opcional: MCP `memory` para consultar diagnósticos anteriores.

### Configuração do MCP gcp-observability
```json
"gcp-observability": {
  "command": "npx",
  "args": ["-y", "google-cloud-observability-mcp@latest"],
  "env": {
    "GOOGLE_APPLICATION_CREDENTIALS": "/caminho/absoluto/para/sua/key.json",
    "GOOGLE_CLOUD_PROJECT": "seu-project-id"
  }
}
```
Service Account mínima: `roles/errorreporting.viewer`, `roles/logging.viewer`, `roles/monitoring.viewer`.

## Procedure

### 1. Triagem (GCP Observability MCP)
- Chame `errors_list` ordenado por contagem, limit 1, para obter o grupo de erro mais crítico.
- Se nenhum grupo existir, reporte pipeline saudável e pare.

### 2. Análise (GCP Observability + Memory MCPs)
- Chame `errors_get` com o ID do grupo de erro para extrair stack traces e eventos.
- Identifique: mensagem de erro, arquivo, linha e tipo de exceção.
- Se o MCP `memory` existir, chame `search_nodes` com palavras-chave da mensagem. Se houver entidade relevante, leia as observations em busca de diagnóstico/fix conhecido.

### 2.1 Gate Jev — triagem código vs infra (MCP `jevcore`)
- Chame `jev_ask` com `type: "choice"`:
  - `instructions`: `"O stack trace aponta para código da aplicação ou para infraestrutura (Cloud Run, build, deploy)?"`
  - `criteria`: `{"código": "falha em lógica da aplicação (arquivo/linha de código)", "infraestrutura": "falha de build, deploy, quota, rede ou plataforma"}`
  - `state`: `{"erro": "<mensagem>", "stack_trace": "<resumo do stack>"}`
- **Resultado:**
  - `"código"` → prossiga para o passo 3.
  - `"infraestrutura"` → redirecione para as skills `logs-backend`/`logs-frontend` antes de mexer em código, e pare.
- **Fallback:** Jev indisponível (`None`, erro ou timeout) ⇒ aplicar a heurística atual (stack apontando para Cloud Run/build ⇒ infra). O Jev nunca bloqueia o fluxo.

### 3. Preparação do fix (GitHub MCP)
- Crie a branch via `create_branch` a partir de `main`, com o nome `fix/gcp-<error-group-id>`.
- Localize o arquivo e a linha via `get_file_contents` e `search_code`.
- Consulte os arquivos canônicos do projeto antes de editar (`.python-version`, `requirements*.txt`, `frontend/package.json`, etc., conforme AGENTS.md).

### 4. Implementação do fix (GitHub MCP)
- Edite apenas o necessário (Diff-Only). Preserve type hints (Python) e strict (TypeScript).
- Não hardcode secrets; toda credencial vem de env vars.
- Commite com mensagem descritiva em português, imperativo. Ex.: `Corrige <causa raiz> no <arquivo>`.

### 5. Validação (Playwright MCP)
- Rode a suíte de testes do projeto (backend: `pytest tests/ -q`; frontend: `npm run test`) ou o teste específico relacionado ao fix.
- Se o fix tiver impacto em UI, rode a skill `web-performance-auditor` passando como contexto o fluxo do usuário afetado pelo bug e a URL relevante.
- Colete evidências: resultados de teste, prints de console/network e o antes/depois do fluxo.

### 6. Entrega (GitHub MCP)
- Com os testes passando, chame `create_pull_request` de `fix/gcp-<error-group-id>` para `main`.
- Título descritivo em português, imperativo.
- Corpo do PR com o máximo de evidências:
  - Link do grupo de erro no GCP Error Reporting.
  - Mensagem de erro e stack trace resumido.
  - Arquivo/linha afetados e resumo do fix.
  - Resultados dos testes e da auditoria (se aplicável).
  - Screenshots/prints quando relevantes.

## Output
Um Pull Request no GitHub contendo o fix, os resultados de validação e o link para o grupo de erro do GCP, pronto para revisão.
