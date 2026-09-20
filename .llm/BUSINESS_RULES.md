# Regras de Negócio — RAG Político

## Domínio

Sistema de consulta pública sobre legislação brasileira, combinando dados oficiais
(Câmara, Senado, TSE, CGU, Fact-checkers) com notícias recentes da web.

## Invariantes Fundamentais

### 1. Síntese Hierárquica Multi-Fonte (Regra Central)

Toda resposta **DEVE** sintetizar duas fontes respeitando uma **hierarquia de confiança**:

1. **FONTE PRIMÁRIA — Base Interna** (Pinecone): dados legislativos, votações, declarações
   de bens, checagens. É a verdade factual canônica; nomes, listas, valores, votações e
   datas devem ser ancorados aqui.
2. **FONTE SECUNDÁRIA — Web Recente** (DuckDuckGo): notícias atuais usadas apenas como
   complemento de recência/contexto. NUNCA substitui, contradiz ou sobrescreve a base interna.

O contexto factual interno é **isolado** dos resultados web secundários: em conflito,
prevalece sempre a Base Interna (a divergência é sinalizada). Se a Base Interna não trouxer
dados, a web é usada explicitamente como informação secundária não verificada.

### 2. Anti-Alucinação

> Se perguntado sobre nomes, listas ou valores específicos e não houver comprovação exata
> na Base Interna, NUNCA invente dados. Diga explicitamente o que foi encontrado.

A regra tem **duas camadas**:

1. **Prompt (freio brando):** hardcoded no prompt de síntese hierárquica, centralizado no
   helper `_build_synthesis_prompt()` em `backend/rag/chat.py` (usado por `invoke()` e `stream()`).
2. **Verificação mecânica (G2):** [`jev_check()`](backend/rag/jev_client.py:213) com
   `claim = pergunta/resposta` e `evidence = documentos recuperados`:
   - **Pré-geração** — [`_answerable()`](backend/rag/chat.py:217): base interna insuficiente ou
     contraditória ⇒ retorna `NOT_FOUND_ANSWER` sem gastar síntese Gemini.
   - **Pós-geração** — [`_post_check_ok()`](backend/rag/chat.py:231): resposta contradita pela
     evidência que a gerou (base interna **+ web**, via [`_synthesis_evidence()`](backend/rag/chat.py:231))
     ⇒ substituída por `NOT_FOUND_ANSWER`.
   - Falha do Jev (`None`) ⇒ pipeline nunca quebra: segue com a geração.

### 3. Rastreabilidade de Fontes

Toda resposta carrega `source_documents[]` com metadados de origem.
O frontend renderiza esses metadados como `SourceBadges` clicáveis.
Classificação de fontes em `main.py:parse_source_name()`:

| Pattern no `raw_source` | Tipo | Label |
|--------------------------|------|-------|
| URL http/https | Notícia Web (DuckDuckGo) | Web: {domain} |
| `votacao_` | Câmara dos Deputados | Histórico de Votação |
| `senado` | Senado Federal | Matéria / Discurso |
| `transparencia`, `cgu` | Portal da Transparência (CGU) | Execução Orçamentária |
| `lupa`, `aosfatos` | Agência de Fact-Checking | Checagem de Fatos |
| `tse_bens` | TSE - DivulgaCand | Declaração de Bens |
| `proposicao`, `camara` | Dados Oficiais | Câmara dos Deputados |
| `plano_governo`, `tse` | Dados Oficiais | Plano de Governo |
| fallback | Documento Interno | Base de Conhecimento |

## Regras de Segurança

### Guardrails (backend/api/guardrails.py)

- Query vazia → HTTP 400
- Query > 1000 caracteres → HTTP 400
- Detecção de prompt injection via regex compilado (11 padrões):
  `ignore previous instructions`, `jailbreak`, `DAN mode`, `exec()`, `<script>`, etc.
- Match → HTTP 400 + log de warning com os primeiros 60 chars

### Rate Limiting (slowapi)

| Endpoint | Limite |
|----------|--------|
| `GET /suggestions` | 60/min por IP |
| `POST /chat` | 30/min por IP |
| `POST /chat/stream` | 30/min por IP |

### Anti-Spam Frontend (useChatStore.ts)

- `isLoading` funciona como trava: se `true`, toda chamada a `sendMessageStream` retorna imediatamente
- Impede envio de query vazia ou whitespace-only
- Links sanitizados: apenas `http://` e `https://` são renderizados; todos recebem `noopener noreferrer`

### Sanitização de Output

- Markdown parseado via `marked` (GFM + breaks)
- HTML sanitizado via `DOMPurify` com whitelist de atributos (`target`, `rel`)

## Regras de Sessão

- Máximo de **5 sessões** simultâneas (`MAX_SESSIONS = 5`)
- Cada sessão é identificada por `sess-{random7}` e tem `label` dinâmico
- Label é atualizado com as primeiras 25 chars da primeira pergunta do usuário
- Sessões persistem em `localStorage` (`rag_chat_sessions_v1`)
- "Limpar Sessão" reseta mensagens mas mantém o slot
- "Resumir Conversa" envia prompt automático pedindo síntese em ≤280 caracteres

## Regras de Analytics (Sugestões Populares)

### Registro de Query (backend/api/analytics.py)

1. Query < 5 chars → ignorada
2. **Fuzzy Match** (SequenceMatcher ratio ≥ 0.68) contra queries existentes → incrementa contagem
3. Se não houver match → **Canonização via LLM** (prompt leve) → insere como nova sugestão
4. Frontend exibe top 8 por contagem decrescente

### Cache de Sugestões (Frontend)

- `localStorage` com TTL de 5 minutos (`SUGGESTIONS_TTL_MS = 300_000`)
- Fallback hardcoded com 8 sugestões iniciais (seeds populados no SQLite em `init_analytics_db`)

## Regras de Cache (Backend)

### RAGQueryCache (backend/rag/cache.py)

- Cache em memória (dict Python)
- TTL: 300 segundos (5 min)
- Max: 200 entries
- Chave: `"{model}:{query_normalizado}"` (lowercase, whitespace colapsado)
- Eviction: remove entry mais antiga quando cheio
- Cache é populado após resposta completa (inclui sources serializados)

## Roteamento Semântico (RAG-101)

Antes de acionar qualquer ferramenta, o [`SemanticRouter`](backend/rag/semantic_router.py)
classifica a intenção da consulta de forma determinística (regex + normalização NFKD,
sem custo de LLM):

| Rota | Gatilho | Ferramentas acionadas |
|------|---------|----------------------|
| `RAG` | Domínio legislativo/político (votações, leis, parlamentares, TSE, CGU...) | Pinecone (primária) + DuckDuckGo (secundária) |
| `WEB` | Intenção de recência/notícias (hoje, notícias, recentemente...) | Somente DuckDuckGo |
| `DIRECT` | Saudação/identidade (olá, quem é você, obrigado...) | Nenhuma — LLM direto |

Precedência: sinais de Web vencem o domínio; o domínio vence a conversa casual.
Rota `DIRECT` retorna `source_documents` vazio (sem rastreabilidade de fontes aplicável).

## Retriever Híbrido

### HybridRetriever (backend/rag/retriever.py)

Combina **Dense** (Pinecone VectorStore) + **BM25** (lexical) via **RRF** (Reciprocal Rank Fusion).

- `k_dense = 4`, `k_bm25 = 4`, `rrf_k = 60`
- Se ambos retornam docs → RRF merge
- Se apenas um retorna → top-k desse retriever
- BM25 é construído a partir dos documentos carregados (tokenização: `split()` lowercase)

## Chunking & Recuperação — Avaliação de Recall

Avaliação sistemática das 3 alavancas de recall de chunking aplicadas à codebase:

| Alavanca | Status | Peso | Evidência / Ação |
|----------|--------|------|------------------|
| Chunk semântico (não tamanho fixo) | Implementado | **ALTA** | [`_chunk_documents()`](pipelines/ingestion/pinecone_ingestor.py:88) divide por sentenças completas (`_split_sentences()` + `_chunk_sentences()`) respeitando o orçamento `CHUNK_SIZE=1000`, sem cortar frase no meio. |
| Overlap estratégico entre chunks | Implementado | — | `OVERLAP_SENTENCES=1` em [`pinecone_ingestor.py`](pipelines/ingestion/pinecone_ingestor.py:24) preserva continuidade nas bordas (redundância intencional). |
| Metadata por chunk | Implementado | **MÉDIA** | [`enrich_metadata()`](pipelines/ingestion/pinecone_ingestor.py:73) adiciona `doc_type`/`title`/`date` em todo chunk (ver [`DATA_MODEL.md`](.llm/DATA_MODEL.md)). |

Invariantes:
- Overlap é redundância intencional (coverage de queries cruzadas nas bordas), não lixo.
- Filtro de metadata antecede a busca vetorial (reduz ruído antes do rerank).
- Embedding bom não compensa chunk ruim — o chunking define o teto do recall.
