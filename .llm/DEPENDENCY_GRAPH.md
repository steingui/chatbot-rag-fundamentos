# Grafo de Dependências — RAG Político

## Backend (Python)

### Dependências Externas (`requirements.txt`)

| Pacote | Versão | Uso |
|--------|--------|-----|
| `fastapi` | 0.141.1 | Framework HTTP async |
| `uvicorn` | 0.52.3 | ASGI server |
| `langchain` | 1.3.15 | Core chains/prompts |
| `langchain-classic` | 1.0.8 | `ContextualCompressionRetriever` |
| `langchain-community` | 0.4.2 | `PineconeHybridSearchRetriever` |
| `langchain-pinecone` | 0.2.13 | `PineconeVectorStore`, `PineconeRerank` |
| `pinecone` | — | SDK Pinecone |
| `langchain-openai` | 1.5.1 | `ChatOpenAI` (OpenRouter) |
| `langchain-huggingface` | 1.2.2 | `HuggingFaceEndpointEmbeddings` |
| `pypdf` | 6.16.1 | Extração de texto de PDFs |
| `python-dotenv` | 1.2.3 | Carrega .env |
| `requests` | 2.34.2 | HTTP client (scrapers) |
| `duckduckgo-search` / `ddgs` | 9.15.0 | Busca web (DDGS) |
| `slowapi` | 0.1.10 | Rate limiting por IP |
| `pinecone-text` | 0.9.0 | Sparse encoder |
| `mmh3` | — | Hash para sparse encoding |
| `firebase-admin` | — | Firebase Auth (JWT) |
| `langchain-google-genai` | — | `ChatGoogleGenerativeAI` (fallback) |
| `prompt-injection-detector` | — | Scanner PID (guardrails) |
| `cachetools` | — | `TTLCache` (RAGQueryCache) |
| `tenacity` | — | Retry |
| `httpx` | — | Cliente HTTP (jev_client) |
| `pytest-asyncio` | — | Testes assíncronos no pytest |

### Grafo de Imports Internos

```
backend/api/main.py
├── backend.rag.chat          → init_components, get_rag_chain
├── backend.rag.cache         → global_rag_cache
├── backend.api.analytics     → get_top_suggestions, record_query
├── backend.api.guardrails    → validate_and_sanitize_query
├── backend.api.auth          → get_required_user
└── backend.api.firestore_db  → save_chat_message, get_session_messages

backend/rag/chat.py
├── langchain_pinecone        → PineconeVectorStore, PineconeRerank
├── langchain_community.retrievers → PineconeHybridSearchRetriever
├── langchain_classic.retrievers   → ContextualCompressionRetriever
├── langchain_huggingface     → HuggingFaceEndpointEmbeddings
├── langchain_openai          → ChatOpenAI
├── langchain_google_genai    → ChatGoogleGenerativeAI (fallback)
├── langchain_core.documents  → Document
├── backend.rag.context_window → build_context_window, count_tokens, format_history, max_input_tokens_for_model
├── backend.rag.semantic_router → SemanticRouter, Route
├── backend.rag.sparse_encoder → FastBM25Encoder
├── backend.rag.jev_client    → jev_check, jev_noul, CHECK_*
└── ddgs                      → DDGS (busca web)

backend/rag/context_window.py
└── tiktoken                  → contagem exata de tokens (fallback: proxy determinístico)

backend/rag/cache.py
├── cachetools            → TTLCache
└── backend.rag.jev_client → jev_noul (dedup semântico G7)

backend/api/analytics.py
├── os, random, hashlib, logging, typing (stdlib)
├── curated_prompts.json      → prompts curados (não usa SQLite)
└── backend.rag.jev_client    → jev_choice (canonização de tema G6)

backend/api/guardrails.py
└── fastapi                   → HTTPException

backend/workers/ingestion_worker.py
├── langchain_pinecone        → PineconeVectorStore
└── langchain_huggingface     → HuggingFaceEndpointEmbeddings
```

## Frontend (Node.js / Vite)

### Dependências de Produção (`package.json`)

| Pacote | Uso |
|--------|-----|
| `react` + `react-dom` | UI framework |
| `zustand` | State management (store único) |
| `marked` | Markdown → HTML parser |
| `dompurify` | Sanitização HTML (XSS prevention) |
| `lucide-react` | Biblioteca de ícones |
| `@tanstack/react-virtual` | Virtualização de listas (MessageList) |

### Dependências de Dev

| Pacote | Uso |
|--------|-----|
| `vite` | Build tool + dev server |
| `typescript` | Tipagem estática |
| `vitest` | Test runner |
| `@testing-library/react` | Utils de teste |
| `jsdom` | DOM virtual para testes |

### Grafo de Imports Internos

```
App.tsx
├── store/useChatStore.ts
├── components/SessionSidebar.tsx
├── components/ChatHeader.tsx
├── components/MessageList.tsx
├── components/SuggestionGrid.tsx
└── App.css → theme/tokens.css

components/SessionSidebar.tsx
└── store/useChatStore.ts

components/ChatHeader.tsx
├── store/useChatStore.ts
└── components/ModelSelector.tsx

components/MessageList.tsx
├── store/useChatStore.ts
├── components/SourceBadges.tsx
└── @tanstack/react-virtual

components/ModelSelector.tsx
└── store/useChatStore.ts

components/SuggestionGrid.tsx
└── store/useChatStore.ts

components/SourceBadges.tsx
└── (props only, sem store)

store/useChatStore.ts
├── zustand
├── marked
└── dompurify
```

### Vite Build (Chunk Splitting)

```javascript
// vite.config.ts manualChunks
{
  vendor: ['react', 'react-dom'],
  markdown: ['marked', 'dompurify'],
  icons: ['lucide-react'],
  virtual: ['@tanstack/react-virtual']
}
```

Resultado: bundle principal ~13kB gzip.
