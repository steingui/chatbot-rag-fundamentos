# Modelos de Dados — RAG Político

## Frontend (TypeScript)

### Types em `useChatStore.ts`

```typescript
type SuggestionItem = {
  prompt: string;   // Texto da sugestão
  count?: number;   // Contagem de uso (hoje sempre ausente/0 — ver API_CONTRACT.md)
};

type Source = {
  type: string;      // Categoria da fonte (ex: "Câmara dos Deputados")
  label: string;     // Label curto (ex: "Histórico de Votação")
  url?: string;      // Link clicável (pode ser undefined)
  raw_file: string;  // Identificador original do metadata
};

type Message = {
  id: string;              // Timestamp ou 'init'
  role: 'user' | 'bot';
  content: string;         // Markdown raw (renderizado via marked+DOMPurify)
  sources?: Source[];       // Apenas em mensagens bot
  timestamp: Date;
};

type Session = {
  id: string;        // "sess-{crypto.randomUUID()}" (SEC-010)
  label: string;     // Primeiras 25 chars da primeira pergunta ou "Sessão N"
  messages: Message[];
  createdAt: Date;
};
```

### Constantes

```typescript
MAX_SESSIONS = 5
FREE_MODELS = [
  { id: 'gemini-3.7-flash', label: 'gemini-3.7-flash · google' },
  { id: 'gemini-3.6-flash', label: 'gemini-3.6-flash · google' },
  { id: 'gemini-flash-latest', label: 'gemini-flash-latest · google' },
  { id: 'gemini-2.5-flash', label: 'gemini-2.5-flash · google' },
  { id: 'meta-llama/llama-3.3-70b-instruct:free', label: 'llama-3.3-70b · free' },
  { id: 'deepseek/deepseek-r1-distill-llama-70b:free', label: 'deepseek-r1-70b · free' }
]
```

### LocalStorage Keys

| Key | Tipo | TTL | Descrição |
|-----|------|-----|-----------|
| `rag_chat_sessions_v1` | `Session[]` serializado | ∞ | Persistência offline-first das sessões |
| `rag_suggestions_cache_v1` | `{ timestamp, data }` | 5 min | Cache de sugestões populares |

## Backend (Python / Pydantic)

### Pydantic Models (main.py)

```python
class ChatRequest(BaseModel):
    session_id: Optional[str] = "default_session"
    query: str
    model: Optional[str] = None

class SourceObject(BaseModel):
    type: str
    label: str
    url: Optional[str] = None
    raw_file: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceObject]

class SuggestionItem(BaseModel):
    prompt: str
    count: Optional[int] = 0

class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionItem]
```

### Sugestões Populares (backend/api/analytics.py)

Não existe mais `analytics.db` nem `init_analytics_db`. As sugestões são prompts
curados lidos de `backend/api/curated_prompts.json` por `get_top_suggestions(limit)`
(aleatórios, sem contadores de popularidade). `record_query()` é no-op — a query é
persistida no Firestore via `save_chat_message()`.

### RAGQueryCache (in-memory)

```python
cachetools.TTLCache(maxsize=200, ttl=300)  # LRU quando cheio
# key format: "{model_name}:{query_normalizado}"
# value: {"answer": str, "sources": [dict]}
```

### Pinecone Index

- **Index name**: `rag-fundamentos`
- **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dims)
- **Provider**: HuggingFace Inference API
- **Metadata fields** (enriquecidos por [`enrich_metadata()`](pipelines/ingestion/pinecone_ingestor.py:73)):
  - `source` (string com nome/path do arquivo de origem)
  - `doc_type` (string: `votacao` | `senado` | `transparencia` | `fact_check` | `tse_bens` | `proposicao` | `plano_governo` | `interno`)
  - `title` (string — stem do arquivo de origem)
  - `date` (string ISO `YYYY-MM-DD`, extraída do nome do arquivo quando presente)

### LangChain Document

```python
Document(
    page_content="texto do chunk (sentenças completas)",
    metadata={
        "source": "votacao_12345",
        "doc_type": "votacao",
        "title": "votacao_12345",
        "date": "2026-05-12",  # quando presente no nome do arquivo
    }
)
```
