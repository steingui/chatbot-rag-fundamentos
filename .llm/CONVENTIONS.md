# Convenções — RAG Político

## Idioma

- **Código**: variáveis/funções em inglês (`parse_source_name`, `sendMessageStream`)
- **Strings de UI**: português brasileiro
- **Commits**: português
- **Documentação**: português

## Commits

Conventional Commits em português:

```
feat(scope): descrição curta
fix(scope): descrição curta
style(scope): descrição curta
refactor(scope): descrição curta
docs(scope): descrição curta
chore(scope): descrição curta
```

Scopes: `rag`, `api`, `frontend`, `ui`, `pipeline`, `infra`, `security`, `perf`

## Estrutura de Diretórios

```
/
├── .github/workflows/     # CI/CD (GitHub Actions cron jobs)
├── .llm/                  # Documentação para interpretação por LLMs
├── backend/
│   ├── api/               # FastAPI (endpoints, guardrails, analytics)
│   ├── rag/               # Core RAG (chat, retriever, cache)
│   └── workers/           # Workers assíncronos (ingestão)
├── frontend/
│   └── src/
│       ├── components/    # Componentes React
│       ├── store/         # Zustand store
│       └── theme/         # Design tokens (CSS + TS)
├── pipelines/
│   ├── scrapers/          # Scrapers de dados legislativos
│   └── ingestion/         # Embedding + upsert Pinecone
├── data/                  # Dados scraped (JSONs locais)
├── tests/                 # Testes backend
└── docs_projeto/          # Documentação acadêmica do projeto
```

## Naming

### Backend (Python)

- Classes: `PascalCase` (`MultiSourceAgentChain`, `HybridRetriever`, `RAGQueryCache`)
- Funções/métodos: `snake_case` (`get_rag_chain`, `validate_and_sanitize_query`)
- Constantes: `UPPER_SNAKE_CASE` (`EMBEDDING_MODEL`, `INDEX_NAME`, `MAX_SESSIONS`)
- Módulos privados prefixados com `_` (`_retriever`, `_llm`, `_rag_initialized`)

### Frontend (TypeScript/React)

- Componentes: `PascalCase` (`SessionSidebar`, `MessageList`)
- Hooks/stores: `camelCase` prefixado com `use` (`useChatStore`)
- Types: `PascalCase` (`Message`, `Session`, `Source`)
- CSS classes: `kebab-case` (`suggestion-card-item`, `msg-header`)
- Constantes: `UPPER_SNAKE_CASE` (`MAX_SESSIONS`, `FREE_MODELS`, `API_URL`)

## Testes

### Frontend

- Runner: **Vitest**
- Localização: `frontend/src/store/__tests__/`
- Convenção de nome: `*.test.ts`
- Environment: `jsdom`
- Cobertura atual: store utilities + sanitização XSS

### Backend

- Runner: **pytest** (não instalado no venv local, roda no CI)
- Localização: `tests/`

## Build & Deploy

### Frontend

```bash
npm run dev      # Dev server (Vite HMR)
npm run build    # Produção → dist/
npm test         # Vitest
```

### Backend (Local)

```bash
uvicorn backend.api.main:app --reload --port 8000
```

### Backend (Produção)

```bash
# Via Docker (multi-stage build)
docker build -t rag-api .
docker run -p 10000:10000 --env-file .env rag-api
```

### Deploy

Push para `main` → Render autodeploy:
- API: rebuild Docker → `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 10000`
- Frontend: `npm install && npm run build` → serve `dist/` como static site

## Segurança

- Nunca commitar `.env` (está no `.gitignore`)
- Variáveis sensíveis via Render Dashboard (secrets)
- Docker roda como `appuser` (non-root)
- CORS aberto (`*`) pois frontend é static site em domínio diferente
- Rate limiting via `slowapi` (por IP)
