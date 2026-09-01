# Arquitetura — RAG Político

## Visão Geral

Monorepo com 3 camadas: **Backend Python** (FastAPI no GCP Cloud Run), **Frontend React** (Vite + Tailwind CSS no Firebase Hosting), **Pipelines de Ingestão** (scrapers + Pinecone Vector DB).

```
┌─────────────────────────────────────────────────────────────────┐
│                     INFRAESTRUTURA GCP                          │
│  ┌──────────────────┐           ┌────────────────────────────┐  │
│  │ Firebase Hosting │           │ GCP Cloud Run              │  │
│  │ (Frontend v2)    │──HTTP────▶│ (FastAPI Container :10000) │  │
│  │ React + Tailwind │           │                            │  │
│  └──────────────────┘           └─────────┬──────────────────┘  │
└─────────────────────────────────────────────┼────────────────────┘
                                              │
                      ┌───────────────────────┼──────────────────┐
                      │                       │                  │
               ┌──────▼──────┐  ┌─────────────▼───┐  ┌──────────▼───┐
               │  Pinecone   │  │  OpenRouter API │  │   DuckDuckGo │
               │ (rag-funds) │  │ (LLM Free Tier) │  │   (DDGS)     │
               └─────────────┘  └─────────────────┘  └──────────────┘
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

## Camada Frontend (v2)

```
frontend/src/
├── App.tsx               # Layout root: Sidebar + ChatPanel + InputForm
├── index.css             # Diretivas do Tailwind CSS v3 e fontes
├── store/
│   └── useChatStore.ts   # Zustand store: sessions, streaming SSE, persistência
├── components/
│   ├── SessionSidebar.tsx  # Sidebar com sessões, resumir, fonte e botões arredondados
│   ├── ChatHeader.tsx      # Header com pílulas de status e model selector
│   ├── MessageList.tsx     # Lista virtualizada de mensagens (TanStack Virtual)
│   ├── ModelSelector.tsx   # Dropdown de modelos free-tier em pílula
│   ├── SuggestionGrid.tsx  # Faixa horizontal de sugestões populares em pílulas
│   ├── SourceBadges.tsx    # Chips de fontes em tons pastel por categoria
│   └── IntroModal.tsx      # Modal de transparência e introdução ao RAG
└── lib/
    └── utils.ts           # Utilitários de fusão de classes (clsx + tailwind-merge)
```

## Infraestrutura

| Componente | Tecnologia | Plataforma / Endpoint |
|-----------|-----------|-----------------------|
| API Backend | FastAPI (Python 3.11) | GCP Cloud Run (`southamerica-east1`) |
| Frontend | React + Tailwind CSS v3 | Firebase Hosting (`chatbot-rag-fundamentos`) |
| CI/CD & Build | Cloud Build | Trigger automático na `main` (`cloudbuild.yaml`) |
| Vector DB | Pinecone (index: `rag-fundamentos`) | Pinecone Serverless |
| LLMs | OpenRouter (modelos :free) | Gemma 4, Llama 3.3, DeepSeek R1, Nemotron |
