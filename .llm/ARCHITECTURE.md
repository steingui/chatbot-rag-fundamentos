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
│   ├── analytics.py      # Sugestões curadas (curated_prompts.json); record_query é no-op
│   ├── guardrails.py     # Validação anti-injection, sanitização, limites
│   ├── auth.py           # Validação obrigatória de JWT do Firebase Auth (get_required_user)
│   └── firestore_db.py   # Persistência de mensagens/sessões de chat no Firestore
├── rag/
│   ├── chat.py           # MultiSourceAgentChain: orquestra Pinecone + DDGS + LLM
│   ├── semantic_router.py # RAG-101: classifica intenção (RAG vs Web vs Direct) antes das ferramentas
│   ├── context_window.py # RAG-109: janela de contexto dinâmica por contagem exata de tokens
│   ├── retriever.py      # HybridRetriever: Dense + BM25 local via RRF (dead code, não instanciado)
│   ├── llm_fallback.py   # DynamicFallbackLLMManager (dead code, não instanciado)
│   └── cache.py          # RAGQueryCache: cache em memória com TTL e eviction LRU
└── workers/
    └── ingestion_worker.py  # Worker assíncrono para ingestão batch no Pinecone
```

### Fluxo de Requisição (POST /chat/stream)

1. `guardrails.validate_and_sanitize_query()` — sanitiza input, bloqueia injection
2. `global_rag_cache.get()` — verifica cache (TTL 5min, chave = `model:query_normalizado`)
3. Se cache miss: `init_components()` lazy → inicializa Pinecone + LLM
4. `get_rag_chain(session_id, model)` → retorna `MultiSourceAgentChain`
5. `chain.stream()` → roteia por `SemanticRouter.route(query)` (RAG vs Web vs Direct):
   a. Rota RAG → `PineconeHybridSearchRetriever` (top_k=30) + `PineconeRerank` (bge-reranker-v2-m3, top_n=5) + filtro G3 (`RERANK_NOUL_THRESHOLD`) como fonte primária
   b. Rota RAG/Web → `_buscar_noticias_web(query)` (DDGS text + news fallback, região BR)
   c. Rota Direct → LLM direto, sem ferramentas
   d. `_build_synthesis_prompt()` → prompt de síntese hierárquica (histórico recente podado por tokens exatos + base factual interna = primário; web = secundário)
   e. `llm.stream(prompt)` → gera tokens incrementais
6. SSE events: `{type: "sources", sources: [...]}` → `{type: "token", token: "..."}` → `[DONE]`
7. `global_rag_cache.set()` — armazena resposta completa
8. `record_query()` em background — no-op (`pass`); persistência fica no Firestore via `save_chat_message()`

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
| LLMs | Google AI & OpenRouter | Gemini (3.7/3.6/2.5 Flash, Flash Latest, 3.5 Flash, Pro Latest), Llama 3.3, DeepSeek R1, Qwen 2.5 Coder |
