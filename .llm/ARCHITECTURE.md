# Arquitetura — RAG Político

## Visão Geral

Monorepo com 3 camadas: **Backend Python** (FastAPI), **Frontend React** (Vite), **Pipelines de Ingestão** (scrapers + Pinecone).
Deploy via Render (Docker para API, static site para frontend).

```
┌─────────────────────────────────────────────────────────────────┐
│                        RENDER (Cloud)                           │
│  ┌──────────────────┐           ┌────────────────────────────┐  │
│  │ chatbot-rag-front│           │ chatbot-rag-api            │  │
│  │ (Static Site)    │──HTTP────▶│ (Docker · FastAPI · :10000)│  │
│  │ Vite + React     │           │                            │  │
│  └──────────────────┘           └─────────┬──────────────────┘  │
└─────────────────────────────────────────────┼────────────────────┘
                                              │
                     ┌────────────────────────┼──────────────────┐
                     │                        │                  │
              ┌──────▼──────┐  ┌──────────────▼───┐  ┌──────────▼───┐
              │  Pinecone   │  │  OpenRouter API   │  │   DuckDuckGo │
              │ (rag-funds) │  │ (LLM Free Tier)   │  │   (DDGS)     │
              └─────────────┘  └───────────────────┘  └──────────────┘
```

## Camadas do Backend

```
backend/
├── api/
│   ├── main.py           # FastAPI app, rotas /chat, /chat/stream, /suggestions
│   ├── analytics.py      # SQLite: registro e canonização de queries populares
│   └── guardrails.py     # Validação anti-injection, sanitização, limites
├── rag/
│   ├── chat.py           # MultiSourceAgentChain: orquestra Pinecone + DDGS + LLM
│   ├── retriever.py      # HybridRetriever: Dense (Pinecone) + BM25 com RRF
│   └── cache.py          # RAGQueryCache: cache em memória com TTL e eviction LRU
└── workers/
    └── ingestion_worker.py  # Worker assíncrono para ingestão batch no Pinecone
```

### Fluxo de Requisição (POST /chat/stream)

1. `guardrails.validate_and_sanitize_query()` — sanitiza input, bloqueia injection
2. `global_rag_cache.get()` — verifica cache (TTL 5min, chave = `model:query_normalizado`)
3. Se cache miss: `init_components()` lazy → inicializa Pinecone + LLM
4. `get_rag_chain(session_id, model)` → retorna `MultiSourceAgentChain`
5. `chain.stream()` →
   a. `_retriever.invoke(query)` → busca vetorial (Pinecone VectorStore)
   b. `_buscar_noticias_web(query)` → DDGS text + news fallback (região BR)
   c. Monta prompt de síntese com 2 blocos de contexto (interno + web)
   d. `llm.stream(prompt)` → gera tokens incrementais
6. SSE events: `{type: "sources", sources: [...]}` → `{type: "token", token: "..."}` → `[DONE]`
7. `global_rag_cache.set()` — armazena resposta completa
8. `record_query()` em background — atualiza SQLite analytics

### LLM Strategy (Multi-Provider Fallback)

```python
primary  = nvidia/nemotron-3-nano-30b-a3b:free
fallback1 = meta-llama/llama-3.3-70b-instruct:free
fallback2 = deepseek/deepseek-r1:free
```

Cadeia via `primary.with_fallbacks([fallback1, fallback2])`.
O modelo pode ser sobrescrito pelo frontend via campo `model` no payload.

## Camada Frontend

```
frontend/src/
├── App.tsx               # Layout root: Sidebar + ChatPanel + InputForm
├── App.css               # Stylesheet principal (todas as classes CSS)
├── store/
│   └── useChatStore.ts   # Zustand store: sessions, streaming SSE, persistência
├── components/
│   ├── SessionSidebar.tsx  # Sidebar com sessões, resumir, limpar
│   ├── ChatHeader.tsx      # Header com título, model selector, badge Pinecone
│   ├── MessageList.tsx     # Lista virtualizada de mensagens (TanStack Virtual)
│   ├── ModelSelector.tsx   # Dropdown de modelos free-tier
│   ├── SuggestionGrid.tsx  # Grid de sugestões populares com badges de contagem
│   └── SourceBadges.tsx    # Chips de fontes com links validados
└── theme/
    ├── tokens.css         # CSS custom properties (design tokens)
    └── tokens.ts          # TypeScript design tokens tipados
```

## Pipelines de Ingestão (CI/CD)

```
pipelines/
├── scrapers/
│   ├── scraper_camara.py         # Votações da Câmara dos Deputados
│   ├── scraper_senado.py         # Matérias e discursos do Senado Federal
│   ├── scraper_tse_bens.py       # Declarações de bens (TSE DivulgaCand)
│   ├── scraper_tse_pdfs.py       # Planos de governo em PDF
│   ├── scraper_transparencia.py  # Portal da Transparência (CGU)
│   └── scraper_rss.py            # Feeds RSS de fact-checking
└── ingestion/
    └── pinecone_ingestor.py      # Embedding (HF all-MiniLM-L6-v2) + upsert Pinecone
```

Triggers via GitHub Actions:
- `ingest_diario_camara.yml` — diário
- `ingest_diario_senado.yml` — diário
- `ingest_semanal_tse.yml` — semanal
- `ingest_semanal_transparencia.yml` — semanal
- `ingest_mensal_pdfs.yml` — mensal

## Infraestrutura

| Componente | Tecnologia | Plano |
|-----------|-----------|-------|
| API Backend | Render Web Service (Docker) | Free |
| Frontend | Render Static Site (Vite build) | Free |
| Vector DB | Pinecone (index: `rag-fundamentos`) | Free |
| LLMs | OpenRouter (modelos :free) | Free |
| Embeddings | HuggingFace Inference (all-MiniLM-L6-v2) | Free |
| CI/CD | GitHub Actions (cron schedules) | Free |
| Analytics | SQLite embedded (analytics.db) | Local |

## Variáveis de Ambiente

| Variável | Onde | Descrição |
|----------|------|-----------|
| `PINECONE_API_KEY` | Render/CI | Chave da API Pinecone |
| `PINECONE_INDEX_NAME` | Render | Nome do index (`rag-fundamentos`) |
| `OPENROUTER_API_KEY` | Render | Chave OpenRouter para LLMs |
| `HF_TOKEN` | Render/CI | Token HuggingFace para embeddings |
| `VITE_API_URL` | Frontend build | URL base da API (default: produção Render) |
