# Modelos de Dados — RAG Político

## Frontend (TypeScript)

### Types em `useChatStore.ts`

```typescript
type SuggestionItem = {
  prompt: string;  // Texto da sugestão
  count: number;   // Contagem de uso
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
  id: string;        // "sess-{random7}" (ex: "sess-a3k9f2x")
  label: string;     // Primeiras 25 chars da primeira pergunta ou "Sessão N"
  messages: Message[];
  createdAt: Date;
};
```

### Constantes

```typescript
MAX_SESSIONS = 5
FREE_MODELS = [
  'nvidia/nemotron-3-nano-30b-a3b:free',
  'meta-llama/llama-3.3-70b-instruct:free',
  'deepseek/deepseek-r1:free',
  'google/gemini-2.0-flash-exp:free',
  'qwen/qwen-2.5-72b-instruct:free'
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
    count: int

class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionItem]
```

### SQLite Schema (analytics.db)

```sql
CREATE TABLE query_stats (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_prompt  TEXT UNIQUE NOT NULL,     -- Texto canonizado da consulta
    count            INTEGER DEFAULT 1,         -- Contagem de uso
    category         TEXT DEFAULT 'geral',      -- Categoria temática
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Seeds iniciais (populados em `init_analytics_db`):

| canonical_prompt | count | category |
|-----------------|-------|----------|
| Resuma a PEC 45/2019 e a reforma tributária | 24 | economia |
| Como os deputados votaram sobre o arcabouço fiscal? | 18 | legislativo |
| Quais bens foram declarados nas eleições recentes pelo TSE? | 12 | tse |
| O que a agência Lupa checou sobre imposto de renda? | 8 | fact-checking |

### RAGQueryCache (in-memory)

```python
_cache: Dict[str, Tuple[float, Any]]
# key format: "{model_name}:{query_normalizado}"
# value: (unix_timestamp, {"answer": str, "sources": [dict]})
```

### Pinecone Index

- **Index name**: `rag-fundamentos`
- **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dims)
- **Provider**: HuggingFace Inference API
- **Metadata fields**: `source` (string com nome/path do arquivo de origem)

### LangChain Document

```python
Document(
    page_content="texto do chunk",
    metadata={"source": "votacao_12345"}  # ou URL, ou nome de arquivo
)
```
