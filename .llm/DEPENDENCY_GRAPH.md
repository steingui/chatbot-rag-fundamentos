# Grafo de Dependências — RAG Político

## Backend (Python)

### Dependências Externas (`requirements.txt`)

| Pacote | Versão | Uso |
|--------|--------|-----|
| `fastapi` | latest | Framework HTTP async |
| `uvicorn` | latest | ASGI server |
| `langchain` | latest | Core chains/prompts |
| `langchain-classic` | latest | Compatibilidade LangChain |
| `langchain-community` | latest | Retrievers comunitários |
| `langchain-pinecone` | latest | PineconeVectorStore |
| `pinecone-client` | latest | SDK Pinecone |
| `langchain-openai` | latest | ChatOpenAI (OpenRouter) |
| `langchain-huggingface` | latest | HuggingFaceEndpointEmbeddings |
| `pypdf` | latest | Extração de texto de PDFs |
| `python-dotenv` | latest | Carrega .env |
| `requests` | latest | HTTP client (scrapers) |
| `duckduckgo-search` | latest | Busca web (import ddgs) |
| `ddgs` | latest | Wrapper DDGS alternativo |
| `slowapi` | latest | Rate limiting por IP |
| `rank-bm25` | latest | BM25Okapi para retrieval lexical |

### Grafo de Imports Internos

```
backend/api/main.py
├── backend.rag.chat          → init_components, get_rag_chain
├── backend.rag.cache         → global_rag_cache
├── backend.api.analytics     → get_top_suggestions, record_query
└── backend.api.guardrails    → validate_and_sanitize_query

backend/rag/chat.py
├── langchain_pinecone        → PineconeVectorStore
├── langchain_huggingface     → HuggingFaceEndpointEmbeddings
├── langchain_openai          → ChatOpenAI
├── langchain_core.documents  → Document
└── ddgs                      → DDGS (busca web)

backend/rag/retriever.py
├── langchain_core.documents  → Document
└── rank_bm25                 → BM25Okapi

backend/rag/cache.py
└── (sem dependências externas, apenas stdlib)

backend/api/analytics.py
├── sqlite3
├── difflib                   → SequenceMatcher (fuzzy match)
└── langchain_openai          → ChatOpenAI (canonização via LLM)

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
