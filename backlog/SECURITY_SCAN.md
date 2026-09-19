# Auditoria Global de Segurança — chatbot-rag-fundamentos

> Data: 2026-09-19 (atualização) · automação [`security-scan`](../../.roo/skills/security-scan/SKILL.md)
> Escopo: SAST, SCA, IaC/Containers, CI/CD, Configs & Git, Lógica RAG & Endpoints.

---

## Resumo Executivo

| Severidade | Qtd. | Síntese |
|-----------|------|---------|
| 🔴 Crítico | 1 | Worker Pool autônomo ainda roda sem `dry-run` (métrica de confiança já corrigida) |
| 🟠 Alto | 4 | Histórico Firestore sem sanitização no prompt · vazamento de erro interno no stream · fallback `sk-dummy` · headers sem CSP/HSTS |
| 🟡 Médio | 5 | Rate limit por IP · cache compartilhado entre usuários · dependências não pinadas · pickle de terceiros · actions sem pinagem SHA |
| 🟢 Baixo | 4 | `_session_agents` sem bound · URL hardcoded no mobile · CORS sem cache-busting · código morto |

> **Resolvidos desde a última auditoria:** `venv/` rastreado (C-01), Cloud Run público (C-02),
> push direto na `main` do pipeline de prompts (C-03) e degradação silenciosa de token inválido (M-02).
> Detalhes na seção [Resolvidos](#-resolvidos-desde-a-última-auditoria).

---

## 🔴 Crítico

### C-04 — Worker Pool autônomo sem `dry-run` por padrão (métrica de confiança já corrigida)
- **Local**: [`autonomous_qa_pipeline.yml`](.github/workflows/autonomous_qa_pipeline.yml:48) executa [`agent_pool.py`](scripts/agent_pool.py:1) sem `--dry-run`; o fluxo de commit/push/PR está em [`process_issue_worker()`](scripts/agent_pool.py:65).
- **Status**: **parcialmente mitigado** — a fórmula [`calculate_confidence_score()`](scripts/agent_pool.py:46) foi corrigida (exige suíte de testes verde para atingir 85%: 40% sintaxe + 40% testes + 10% diff + 10% bônus), com regressão em [`test_security_critical.py`](tests/test_security_critical.py:121). Porém o pipeline diário ainda roda o worker com poder de commit/push/PR sem revisão humana.
- **Impacto**: o bot abre PRs e faz push de alterações geradas por agente; embora a métrica agora bloqueie sem testes verdes, a execução autônoma de alteração de código permanece ativa em cron.
- **Mitigação**: rodar o workflow com `python3 scripts/agent_pool.py --dry-run` por padrão (ou remover o push/PR do cron) e exigir aprovação humana antes de qualquer alteração.

---

## 🟠 Alto

### A-01 — Histórico de sessão injetado no prompt sem sanitização
- **Local**: [`chat()`](backend/api/main.py:216) carrega [`get_session_messages()`](backend/api/firestore_db.py:39) e injeta em [`_build_synthesis_prompt()`](backend/rag/chat.py:213). A query do usuário é sanitizada por [`validate_and_sanitize_query()`](backend/api/guardrails.py:77), mas **as respostas do assistant não são** — e elas voltam ao contexto no turno seguinte.
- **Impacto**: injeção de prompt auto-propagada (a resposta do LLM pode conter instruções que condicionam o próximo turno) e cross-turn injection via conteúdo de `assistant`.
- **Mitigação**: delimitar e escapar o bloco de histórico (ex.: truncar, remover padrões de injeção ou usar estrutura de mensagens com roles bem separadas em vez de texto plano); nunca tratar histórico como texto de confiança.

### A-02 — Vazamento de mensagem de erro interna no stream
- **Local**: [`chat_stream()`](backend/api/main.py:306) devolve `f"\n[Erro no processamento: {stream_err}]"` ao cliente.
- **Impacto**: expõe detalhes internos (exceções, caminhos, nomes de módulos) para o atacante, útil em reconhecimento.
- **Mitigação**: retornar mensagem genérica e logar o detalhe no servidor:
  ```python
  err_payload = {"type": "token", "token": "\n[Erro interno. Tente novamente.]"}
  ```

### A-03 — Fallback com chave dummy `sk-dummy`
- **Local**: [`get_rag_chain()`](backend/rag/chat.py:356) e [`get_llm_instance()`](backend/rag/llm_fallback.py:22).
- **Impacto**: máscara falhas de configuração (a chamada segue com chave inválida e depende de fallback), além de ser padrão de credencial hardcoded. Sem secret real exposta, mas sinaliza ausência de fail-fast.
- **Mitigação**: se `OPENROUTER_API_KEY` estiver ausente, não instanciar o provedor; logar erro claro em vez de `or "sk-dummy"`.

### A-04 — Headers de segurança incompletos (sem CSP e HSTS)
- **Local**: [`SecurityHeadersMiddleware`](backend/api/main.py:47).
- **Impacto**: existem `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e `Permissions-Policy`, mas faltam **Content-Security-Policy** (mitigação XSS) e **Strict-Transport-Security** (HSTS).
- **Mitigação**: adicionar `Content-Security-Policy` restritiva e `Strict-Transport-Security: max-age=31536000; includeSubDomains`.

---

## 🟡 Médio

### M-01 — Rate limiting apenas por IP
- **Local**: [`limiter = Limiter(key_func=get_remote_address)`](backend/api/main.py:22).
- **Impacto**: atrás de proxy, todos os clientes podem compartilhar o mesmo IP; anônimos burlam o limite trocando de IP. Sem limite por chave/sessão.
- **Mitigação**: usar `X-Forwarded-For` confiável e adicionar limite por `user_id` autenticado.

### M-03 — Cache compartilhado entre usuários (cache poisoning)
- **Local**: [`global_rag_cache`](backend/rag/cache.py:34) usa chave apenas `(query, model)` — [`_normalize_key()`](backend/rag/cache.py:13) — sem `user_id`.
- **Impacto**: a resposta de uma query é servida a todos os usuários; se o LLM gerar conteúdo malicioso para uma query, ele fica cached e é distribuído (mesmo com allowlist de modelos em [`ALLOWED_MODELS`](backend/api/main.py:60)).
- **Mitigação**: incluir `user_id` na chave ou, no mínimo, sanitizar a resposta antes de cachear.

### M-04 — Dependências não pinadas
- **Local**: [`requirements.txt`](requirements.txt:9) (`pinecone`, `duckduckgo-search`, `rank-bm25`, `firebase-admin`, `langchain-google-genai`, `mmh3`, `prompt-injection-detector`, `cachetools`, `tenacity`) e caret-ranges no [`frontend/package.json`](frontend/package.json:14).
- **Impacto**: builds não reprodutíveis e risco de introdução de CVE via resolução transitiva nova.
- **Mitigação**: pinar versões exatas (`pip freeze`) e usar lockfile no frontend (`package-lock.json` já existe — garantir `npm ci`).

### M-05 — Desserialização de pickle de terceiros
- **Local**: [`_get_pid_scanner()`](backend/api/guardrails.py:63) carrega `model.pkl`/`vectorizer.pkl` via `pickle` do pacote [`prompt-injection-detector`](requirements.txt:21).
- **Impacto**: pickle é RCE-equivalente se o artefato for comprometido na cadeia de dependência.
- **Mitigação**: aceitar o risco documentado ou substituir por artefato serializado em formato seguro (ONNX/safetensors).

### M-06 — GitHub Actions sem pinagem por SHA
- **Local**: `uses: actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4` em todos os workflows (ex.: [`ingest_diario_camara.yml`](.github/workflows/ingest_diario_camara.yml:18)) e `node-version: 'latest'` em [`ingest_diario_camara.yml`](.github/workflows/ingest_diario_camara.yml:23).
- **Impacto**: risco de supply chain (tag móvel) e builds não reprodutíveis.
- **Mitigação**: pinar actions por commit SHA e fixar `node-version` (ex.: `22`).

---

## 🟢 Baixo

### B-01 — `_session_agents` sem bound
- **Local**: [`_session_agents`](backend/rag/chat.py:28) cresce indefinidamente em [`get_rag_chain()`](backend/rag/chat.py:371).
- **Impacto**: memory leak gradual em serviço de longa duração.
- **Mitigação**: usar `TTLCache`/LRU para agentes por sessão.

### B-02 — URL da API hardcoded no mobile
- **Local**: [`mobile/src/services/api.ts`](mobile/src/services/api.ts:3) usa `http://localhost:10000` com comentário de prod.
- **Impacto**: app mobile apontaria para localhost em produção (não funcional); expõe a URL da API em plaintext no bundle (não é secret, mas facilita reconhecimento).
- **Mitigação**: injetar via variável de ambiente de build (`EXPO_PUBLIC_API_URL`).

### B-03 — Cabeçalhos de cache `immutable` sem hash de arquivo
- **Local**: [`firebase.json`](firebase.json:29) aplica `max-age=31536000, immutable` a `**/*.@(js|css|map)`.
- **Impacto**: se os bundles não usam hash no nome, atualizações podem ser servidas stale por um ano.
- **Mitigação**: garantir filenames hasheados no build do Vite (padrão) ou reduzir TTL.

### B-04 — Código morto / atribuição duplicada
- **Local**: [`init_components()`](backend/rag/chat.py:76-78) atribui `api_key` duas vezes; [`record_query()`](backend/api/analytics.py:26) é no-op.
- **Impacto**: ruído que dificulta auditoria; sem impacto direto de segurança.
- **Mitigação**: limpar no próximo refactor.

---

## ✅ Resolvidos desde a última auditoria

### C-01 — `venv/` versionado no repositório — **RESOLVIDO**
- Commit `383eb53` (`chore: remove venv/ do controle de versão`). `git ls-files venv/` retorna 0 arquivos; `venv/` permanece no [`.gitignore`](.gitignore:1).

### C-02 — API Cloud Run pública (`--allow-unauthenticated`) — **RESOLVIDO**
- Commit `95f4871` (`fix: exige autenticação no chat e fecha Cloud Run público`).
- [`cloudbuild.yaml`](cloudbuild.yaml:29) e [`scripts/setup-gcp.sh`](scripts/setup-gcp.sh:76) agora usam `--no-allow-unauthenticated`.
- Ambos os endpoints exigem [`get_required_user()`](backend/api/auth.py:64): [`chat()`](backend/api/main.py:196) e [`chat_stream()`](backend/api/main.py:249). Regressão em [`test_security.py`](tests/test_security.py:33) (401 sem token).

### C-03 — Pipeline de prompts com push direto na `main` — **RESOLVIDO**
- Commit `5596441` (`fix: troca push direto por PR no pipeline de prompts`).
- [`generate_dynamic_prompts.yml`](.github/workflows/generate_dynamic_prompts.yml:37) agora usa `peter-evans/create-pull-request@v6` e abre PR para revisão humana em vez de commitar/pushar direto na `main`. Mantém `contents: write` apenas para criar a branch da PR.

### M-02 — Token inválido degrada silenciosamente para anônimo — **RESOLVIDO**
- [`get_required_user()`](backend/api/auth.py:64) agora é usado nos endpoints de chat; token inválido/ausente retorna **401** em vez de degradar para anônimo.

> **Nota (escopo fora da segurança):** a árvore de trabalho também contém correções da auditoria
> de Perf/SEO (issue [#8](https://github.com/steingui/chatbot-rag-fundamentos/issues/8)) ainda não
> commitadas: `VITE_API_URL` com sufixo `/api/v1/chat` em [`cloudbuild.yaml`](cloudbuild.yaml:46),
> metadados SEO em [`frontend/index.html`](frontend/index.html:7) e rewrites/arquivos `robots.txt`/`sitemap.xml`
> em [`firebase.json`](firebase.json:13) e `frontend/public/`.

---

## O que está correto (não alterar)

- **Firestore isolado**: [`firestore.rules`](firestore.rules:8) com `allow read, write: if false` — clientes nunca acessam direto; só o backend via Admin SDK.
- **CORS restrito**: [`ALLOWED_ORIGINS`](backend/api/main.py:35) com domínios conhecidos e `allow_credentials=False`.
- **Allowlist de modelos**: [`ALLOWED_MODELS`](backend/api/main.py:60) previne cache poisoning por modelo arbitrário.
- **XSS no frontend mitigado**: [`formatMarkdown()`](frontend/src/store/useChatStore.ts:76) aplica [`DOMPurify.sanitize()`](frontend/src/store/useChatStore.ts:79) com teste dedicado em [`useChatStore.test.ts`](frontend/src/store/__tests__/useChatStore.test.ts:19).
- **Secrets via env/Secret Manager**: [`sync_secrets.sh`](scripts/sync_secrets.sh:1) e [`cloudbuild.yaml`](cloudbuild.yaml:35) usam `--set-secrets`; `.env.example` sem valores reais.
- **Usuário não-root no container**: [`Dockerfile`](Dockerfile:33) executa como `appuser` com `HEALTHCHECK`.
- **`.dockerignore`/`.gcloudignore`** excluem `.env` e artefatos do build.
- **Autenticação obrigatória nos endpoints de chat**: [`get_required_user()`](backend/api/auth.py:64) em [`chat()`](backend/api/main.py:196) e [`chat_stream()`](backend/api/main.py:249).

---

## Plano de Ação Priorizado

| Ordem | Item | Severidade | Esforço |
|-------|------|-----------|---------|
| 1 | Sanitizar/delimitar histórico no prompt de síntese | 🟠 A-01 | Médio |
| 2 | Mensagem genérica no stream + CSP/HSTS | 🟠 A-02/A-04 | Baixo |
| 3 | Remover `sk-dummy` (fail-fast) | 🟠 A-03 | Baixo |
| 4 | Rodar worker pool com `--dry-run` por padrão no cron | 🔴 C-04 | Baixo |
| 5 | Incluir `user_id` na chave de cache | 🟡 M-03 | Baixo |
| 6 | Rate limit por `user_id` autenticado (além do IP) | 🟡 M-01 | Médio |
| 7 | Pinar dependências e actions por SHA | 🟡 M-04/M-06 | Médio |
| 8 | Substituir artefato pickle do PID scanner | 🟡 M-05 | Médio |
| 9 | Bound no `_session_agents` + limpeza de código morto | 🟢 B-01/B-04 | Baixo |
