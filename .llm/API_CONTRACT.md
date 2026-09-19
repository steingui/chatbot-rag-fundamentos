# Contrato da API — RAG Político

Base URL de produção: `https://chatbot-rag-api-1043919586992.southamerica-east1.run.app`

## Endpoints

---

### `GET /`

Health check.

**Response** `200`:
```json
{ "status": "ok", "message": "API RAG rodando no Cloud Run" }
```

---

### `GET /api/v1/suggestions`

Retorna as 8 consultas mais populares.
Rate limit: **60/min** por IP.

**Response** `200`:
```json
{
  "suggestions": [
    { "prompt": "Resuma a PEC 45/2019 e a reforma tributária", "count": 25 },
    { "prompt": "Como os deputados votaram sobre o arcabouço fiscal?", "count": 18 }
  ]
}
```

---

### `POST /api/v1/chat`

Consulta síncrona (resposta completa de uma vez).
Rate limit: **30/min** por IP.

**Autenticação**:
- Opcional. Sem `Authorization`, o usuário é tratado como `anonymous`.
- Com `Authorization: Bearer <id_token>` (Firebase Auth), o backend valida o
  token e injeta `uid`, `email`, `name` e `privileges` (custom claims) no contexto.

**Request Body**:
```json
{
  "session_id": "sess-abc1234",    // optional, default: "default_session"
  "query": "Como votaram a PEC 45?",
  "model": "meta-llama/llama-3.3-70b-instruct:free"  // optional
}
```

**Response** `200`:
```json
{
  "answer": "Texto da resposta sintetizada...",
  "sources": [
    {
      "type": "Câmara dos Deputados",
      "label": "Histórico de Votação",
      "url": "https://www.camara.leg.br/proposicoesWeb/...",
      "raw_file": "votacao_12345"
    },
    {
      "type": "Notícia Web (DuckDuckGo)",
      "label": "Web: g1.globo.com",
      "url": "https://g1.globo.com/...",
      "raw_file": "https://g1.globo.com/..."
    }
  ]
}
```

**Errors**:
- `400` — query vazia, > 1000 chars, ou prompt injection detectado
- `429` — rate limit exceeded
- `500` — erro interno

---

### `POST /api/v1/chat/stream`

Consulta com streaming via **Server-Sent Events (SSE)**.
Rate limit: **30/min** por IP.
Content-Type da resposta: `text/event-stream`.

**Autenticação**: mesma de `POST /api/v1/chat` (Bearer opcional).

**Request Body**: mesmo de `POST /api/v1/chat`.

**SSE Events** (cada um em `data: {json}\n\n`):

1. **Sources** (enviado primeiro):
```json
{ "type": "sources", "sources": [ { "type": "...", "label": "...", "url": "...", "raw_file": "..." } ] }
```

2. **Token** (enviado incrementalmente):
```json
{ "type": "token", "token": "fragmento de texto" }
```

3. **Done** (fim do stream):
```
data: [DONE]
```

4. **Erro** (se ocorrer durante streaming):
```json
{ "type": "token", "token": "\n[Erro no processamento: mensagem]" }
```

---

## DTOs (Pydantic Models)

```python
class ChatRequest(BaseModel):
    session_id: Optional[str] = "default_session"
    query: str
    model: Optional[str] = None

class SourceObject(BaseModel):
    type: str       # ex: "Câmara dos Deputados", "Notícia Web (DuckDuckGo)"
    label: str      # ex: "Histórico de Votação", "Web: g1.globo.com"
    url: str | None # link clicável ou null
    raw_file: str   # identificador original do metadata

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceObject]

class SuggestionItem(BaseModel):
    prompt: str
    count: int

class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionItem]
```

## CORS

```python
allow_origins=ALLOWED_ORIGINS   # domínios conhecidos (SEC-001)
allow_credentials=False
allow_methods=["GET", "POST"]
allow_headers=["Content-Type", "Authorization"]
```

> Nota: a validação de `Origin` (`OriginCheckMiddleware`) foi substituída por
> validação de Bearer Token (`SEC-503`). O `Origin` não é mais usado como
> mecanismo de segurança.

## Frontend → Backend Communication

O frontend (`useChatStore.ts`) calcula as URLs assim:

```typescript
API_URL = VITE_API_URL || 'https://chatbot-rag-api-1043919586992.southamerica-east1.run.app/api/v1/chat'
STREAM_API_URL = API_URL + '/stream'      // POST /api/v1/chat/stream
SUGGESTION_API_URL = API_URL → '/suggestions'  // GET /api/v1/suggestions
```

Fluxo preferencial: **SSE streaming** (`/api/v1/chat/stream`).
Fallback: se SSE falhar (`!res.ok || !res.body`), faz POST síncrono em `/api/v1/chat`.
