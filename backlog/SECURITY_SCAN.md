# Auditoria Global de Segurança — chatbot-rag-fundamentos

> Data: automação [`security-scan`](../../.roo/skills/security-scan/SKILL.md)
> Escopo: SAST, SCA, IaC/Containers, CI/CD, Configs & Git, Lógica RAG & Endpoints.

---

## Resumo Executivo

| Severidade | Qtd. | Síntese |
|-----------|------|---------|
| 🔴 Crítico | 4 | `venv/` rastreado no Git · Cloud Run público sem auth · pipeline autônomo com push direto na `main` · QA bot autônomo com métrica de confiança inócua |
| 🟠 Alto | 4 | Histórico Firestore sem sanitização no prompt · vazamento de erro interno no stream · fallback `sk-dummy` · headers sem CSP/HSTS |
| 🟡 Médio | 6 | Rate limit por IP · token inválido vira anônimo · cache compartilhado entre usuários · dependências não pinadas · pickle de terceiros · actions sem pinagem SHA |
| 🟢 Baixo | 4 | `_session_agents` sem bound · URL hardcoded no mobile · CORS sem cache-busting · código morto |

---

## 🔴 Crítico

### C-01 — `venv/` versionado no repositório (1221 arquivos)
- **Local**: [`venv/`](venv/) rastreado no Git apesar do [`gitignore`](.gitignore:1) conter `venv/`.
- **Impacto**: superfície de ataque ampliada (código de terceiros não auditado dentro do repo), risco de secrets/paths locais em `.pth`, `.pyc` e scripts de ativação, e inflação do histórico Git. Qualquer `.env` ou credencial copiada acidentalmente para `venv/` em algum commit ficaria exposta para sempre.
- **Mitigação**:
  ```bash
  git rm -r --cached venv/
  git commit -m "chore: remove venv rastreado do git"
  ```
  Confirmar que `venv/` permanece no `.gitignore` e nunca mais versionar.

### C-02 — API Cloud Run pública (`--allow-unauthenticated`)
- **Local**: [`cloudbuild.yaml`](cloudbuild.yaml:29) e [`scripts/setup-gcp.sh`](scripts/setup-gcp.sh:76).
- **Impacto**: o serviço aceita tráfego sem autenticação. O endpoint [`chat()`](backend/api/main.py:194) usa [`get_optional_user()`](backend/api/auth.py:44), que retorna `None` para anônimos — qualquer pessoa na internet consome LLM/Pinecone/DDGS às custas do projeto, sujeita apenas a rate limit por IP (bypassável).
- **Mitigação**: manter a rota pública apenas se houver intenção explícita de demo; caso contrário exigir [`get_required_user()`](backend/api/auth.py:64) no chat e remover `--allow-unauthenticated`. No mínimo, adicionar quota por projeto e rate limit por `user_id` autenticado.

### C-03 — Pipeline de prompts dinâmicos com push direto na `main`
- **Local**: [`generate_dynamic_prompts.yml`](.github/workflows/generate_dynamic_prompts.yml:11) (`permissions: contents: write`) e o `git push` em [`generate_dynamic_prompts.yml`](.github/workflows/generate_dynamic_prompts.yml:41).
- **Impacto**: um cronjob roda LLM e commita/pusha direto na `main` sem revisão humana. É vetor de **prompt injection persistente**: conteúdo gerado pelo LLM é gravado em [`curated_prompts.json`](backend/api/curated_prompts.json) e depois servido como sugestão no frontend. Um LLM comprometido ou alucinado pode injetar texto malicioso que é renderizado para todos os usuários.
- **Mitigação**: trocar o push por PR (`permissions: contents: read` + `pull-requests: write`) e exigir aprovação; sanitizar/validar o JSON antes do commit.

### C-04 — Worker Pool autônomo com métrica de confiança inócua
- **Local**: [`calculate_confidence_score()`](scripts/agent_pool.py:46) (sempre ≥ 85%: 60% sintaxe + 30% diff + 10% bônus) e o fluxo de commit/push/PR em [`process_issue_worker()`](scripts/agent_pool.py:58).
- **Impacto**: o bot abre PRs e faz push de alterações geradas por agente sem gate real; a métrica nunca bloqueia nada quando há diff válido. Combinado com `GITHUB_TOKEN` no workflow, é superfície de alteração autônoma de código.
- **Mitigação**: desabilitar push/PR automático em produção (`dry_run` por padrão), exigir aprovação humana e reavaliar a fórmula de confiança com checks reais (testes, lint).

---

## 🟠 Alto

### A-01 — Histórico de sessão injetado no prompt sem sanitização
- **Local**: [`chat()`](backend/api/main.py:216) carrega [`get_session_messages()`](backend/api/firestore_db.py:39) e injeta em [`_build_synthesis_prompt()`](backend/rag/chat.py:213). A query do usuário é sanitizada por [`validate_and_sanitize_query()`](backend/api/guardrails.py:77), mas **as respostas do assistant não são** — e elas voltam ao contexto no turno seguinte.
- **Impacto**: injeção de prompt auto-propagada (a resposta do LLM pode conter instruções que condicionam o próximo turno) e cross-turn injection via conteúdo de `assistant`.
- **Mitigação**: delimitar e escapar o bloco de histórico (ex.: truncar, remover padrões de injeção ou usar estrutura de mensagens com roles bem separadas em vez de texto plano); nunca tratar histórico como texto de confiança.

### A-02 — Vazamento de mensagem de erro interna no stream
- **Local**: [`chat_stream()`](backend/api/main.py:310) devolve `f"\n[Erro no processamento: {stream_err}]"` ao cliente.
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

### M-02 — Token inválido degrada silenciosamente para anônimo
- **Local**: [`get_optional_user()`](backend/api/auth.py:44) retorna `None` em token inválido/expirado; [`get_required_user()`](backend/api/auth.py:64) existe mas **não é usado** em nenhum endpoint.
- **Impacto**: rotas que deveriam exigir auth não a exigem de fato; o cliente não distingue "sem token" de "token inválido".
- **Mitigação**: usar `get_required_user` nas rotas sensíveis e retornar 401 para token inválido quando autenticação for obrigatória.

### M-03 — Cache compartilhado entre usuários (cache poisoning)
- **Local**: [`global_rag_cache`](backend/rag/cache.py:34) usa chave apenas `(query, model)` — [`_normalize_key()`](backend/rag/cache.py:13) — sem `user_id`.
- **Impacto**: a resposta de uma query é servida a todos os usuários; se o LLM gerar conteúdo malicioso para uma query, ele fica cached e é distribuído (mesmo com allowlist de modelos em [`ALLOWED_MODELS`](backend/api/main.py:60)).
- **Mitigação**: incluir `user_id` na chave ou, no mínimo, sanitizar a resposta antes de cachear.

### M-04 — Dependências não pinadas
- **Local**: [`requirements.txt`](requirements.txt:9) (`pinecone`, `duckduckgo-search`, `ddgs`, `firebase-admin`, `langchain-google-genai`, `rank-bm25`, `mmh3`, `prompt-injection-detector`, `cachetools`, `tenacity`) e caret-ranges no [`frontend/package.json`](frontend/package.json:14).
- **Impacto**: builds não reprodutíveis e risco de introdução de CVE via resolução transitiva nova.
- **Mitigação**: pinar versões exatas (`pip freeze`) e usar lockfile no frontend (`package-lock.json` já existe — garantir `npm ci`).

### M-05 — Desserialização de pickle de terceiros
- **Local**: [`_get_pid_scanner()`](backend/api/guardrails.py:63) carrega `model.pkl`/`vectorizer.pkl` via `pickle` do pacote [`prompt-injection-detector`](requirements.txt:21).
- **Impacto**: pickle é RCE-equivalente se o artefato for comprometido na cadeia de dependência.
- **Mitigação**: aceitar o risco documentado ou substituir por artefato serializado em formato seguro (ONNX/safetensors).

### M-06 — GitHub Actions sem pinagem por SHA
- **Local**: `uses: actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4` em todos os workflows (ex.: [`ingest_diario_camara.yml`](.github/workflows/ingest_diario_camara.yml:18)) e `node-version: 'latest'`.
- **Impacto**: risk de supply chain (tag móvel) e builds não reprodutíveis.
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
- **Local**: [`firebase.json`](firebase.json:21) aplica `max-age=31536000, immutable` a `**/*.@(js|css|map)`.
- **Impacto**: se os bundles não usam hash no nome, atualizações podem ser servidas stale por um ano.
- **Mitigação**: garantir filenames hasheados no build do Vite (padrão) ou reduzir TTL.

### B-04 — Código morto / atribuição duplicada
- **Local**: [`init_components()`](backend/rag/chat.py:76-78) atribui `api_key` duas vezes; [`record_query()`](backend/api/analytics.py:26) é no-op.
- **Impacto**: ruído que dificulta auditoria; sem impacto direto de segurança.
- **Mitigação**: limpar no próximo refactor.

---

## O que está correto (não alterar)

- **Firestore isolado**: [`firestore.rules`](firestore.rules:8) com `allow read, write: if false` — clientes nunca acessam direto; só o backend via Admin SDK.
- **CORS restrito**: [`ALLOWED_ORIGINS`](backend/api/main.py:35) com domínios conhecidos e `allow_credentials=False`.
- **Allowlist de modelos**: [`ALLOWED_MODELS`](backend/api/main.py:60) previne cache poisoning por modelo arbitrário.
- **XSS no frontend mitigado**: [`formatMarkdown()`](frontend/src/store/useChatStore.ts:76) aplica [`DOMPurify.sanitize()`](frontend/src/store/useChatStore.ts:79) com teste dedicado em [`useChatStore.test.ts`](frontend/src/store/__tests__/useChatStore.test.ts:19).
- **Secrets via env/Secret Manager**: [`sync_secrets.sh`](scripts/sync_secrets.sh:1) e [`cloudbuild.yaml`](cloudbuild.yaml:35) usam `--set-secrets`; `.env.example` sem valores reais.
- **Usuário não-root no container**: [`Dockerfile`](Dockerfile:33) executa como `appuser` com `HEALTHCHECK`.
- **`.dockerignore`/`.gcloudignore`** excluem `.env` e artefatos do build.

---

## Plano de Ação Priorizado

| Ordem | Item | Severidade | Esforço |
|-------|------|-----------|---------|
| 1 | Remover `venv/` do Git (`git rm -r --cached venv/`) | 🔴 C-01 | Baixo |
| 2 | Exigir auth ou fechar `--allow-unauthenticated` no Cloud Run | 🔴 C-02 | Médio |
| 3 | Trocar push direto por PR no pipeline de prompts | 🔴 C-03 | Médio |
| 4 | Desativar execução autônoma do worker pool (dry-run default) | 🔴 C-04 | Baixo |
| 5 | Sanitizar/delimitar histórico no prompt de síntese | 🟠 A-01 | Médio |
| 6 | Mensagem genérica no stream + CSP/HSTS | 🟠 A-02/A-04 | Baixo |
| 7 | Remover `sk-dummy` (fail-fast) | 🟠 A-03 | Baixo |
| 8 | Incluir `user_id` na chave de cache | 🟡 M-03 | Baixo |
| 9 | Pinar dependências e actions por SHA | 🟡 M-04/M-06 | Médio |
