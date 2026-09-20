# 🧠 Backlog 01: RAG, Modelos de IA e Mitigação de Alucinações

> **Objetivo:** Garantir respostas precisas, sem alucinações, com baixo custo e alta resiliência de LLMs.

---

## 🎯 Tarefas & Histórias de Usuário

### 1.1 Roteamento Semântico & Fallbacks (Multi-LLM)
- [x] **[RAG-101]** Implementar roteamento semântico (`SemanticRouter`) para classificar a intenção do usuário antes de acionar ferramentas (RAG vs Web vs Direct LLM).
- [x] **[RAG-113]** Gate Jev no default ambíguo do roteamento com guardrail de 90% de confiança — regex soberano, Jev arbitra só com `confidence >= 0.9`, abaixo disso decider LLM decide e fallback RAG `[DONE]` → [`backend/rag/jev_client.py`](../backend/rag/jev_client.py) + [`backend/rag/semantic_router.py`](../backend/rag/semantic_router.py:126).
- [x] **[RAG-102]** Migrar fallback de OpenRouter Free para Google AI Studio (`gemini-3.7-flash`) como LLM primária `[DONE]` → [`backend/rag/chat.py`](../backend/rag/chat.py:82) (`ChatGoogleGenerativeAI` como primeiro fallback, `_llm = fallbacks[0]`).
- [ ] **[RAG-103]** Integrar Groq (`llama-3.3-70b`) como LLM Fallback 1 para absorção de rate-limits (HTTP 429).
- [ ] **[RAG-104]** Integrar DeepSeek V4 Flash via API direta como Fallback 2 de baixíssimo custo.
- [ ] **[RAG-105]** Configurar transição automática para Gemini 3.7 Paid Tier em picos de tráfego.

### 1.2 Qualidade de Contexto & Reranking
- [x] **[RAG-106]** Integrar Pinecone Hybrid Search (Vetor + BM25 léxico) para termos exatos e nomes de parlamentares.
- [x] **[RAG-107]** Configurar `bge-reranker-v2-m3` nativo no Pinecone para ordenação de relevância pós-recuperação.
- [x] **[RAG-108]** Ajustar prompt de síntese hierárquica isolando contexto factual interno de resultados web secundários.
- [x] **[RAG-109]** Implementar janela de contexto dinâmico baseada em contagem exata de tokens para evitar perda de histórico recente.
- [x] **[RAG-115]** Filtro de relevância pós-rerank (G3): `jev_noul` por documento top-k com limiar `RERANK_NOUL_THRESHOLD = 0.5`, mantendo só os trechos relevantes antes do prompt de síntese `[DONE]` → [`backend/rag/jev_client.py`](../backend/rag/jev_client.py:213) + [`backend/rag/chat.py`](../backend/rag/chat.py:217) + [`tests/test_jev_g3_rerank.py`](../tests/test_jev_g3_rerank.py).
- [x] **[RAG-116]** Gate de web search (G4): `_needs_web_search()` com `jev_noul` ("esta pergunta exige informação recente?") só aciona DDGS na rota RAG quando `noul >= WEB_GATE_NOUL_THRESHOLD`; rota WEB explícita sempre aciona; falha do Jev mantém web `[DONE]` → [`backend/rag/chat.py`](../backend/rag/chat.py:241) + [`tests/test_jev_g4_web_gate.py`](../tests/test_jev_g4_web_gate.py).
- [x] **[RAG-117]** Conflito interno vs web verificado mecanicamente (G5): `_web_conflicts_with_base()` com `jev_check` injeta flag explícita no prompt de síntese para priorizar a base e citar a divergência quando a web contradiz a base `[DONE]` → [`backend/rag/chat.py`](../backend/rag/chat.py:287) + [`tests/test_jev_g5_web_conflict.py`](../tests/test_jev_g5_web_conflict.py).
- [x] **[RAG-121]** Follow-up conversacional (G8): `_FOLLOWUP_RE` em [`semantic_router.py`](../backend/rag/semantic_router.py:64) classifica "fale mais"/"continue"/"explique melhor" como `Route.DIRECT` por regex (custo zero), evitando DDGS com query-lixo; mensagem de erro de streaming separada da resposta parcial `[DONE]` → [`tests/test_followup_direct.py`](../tests/test_followup_direct.py).
- [x] **[RAG-119]** Dedup semântico de cache (G7): `RAGQueryCache._semantic_hit()` com `jev_noul` e limiar `SEMANTIC_DEDUP_THRESHOLD = 0.9` — hit exato continua zero-Jev, miss compara a query nova contra chaves do mesmo `model`, falha do Jev ⇒ miss `[DONE]` → [`backend/rag/cache.py`](../backend/rag/cache.py:25) + [`tests/test_jev_g7_cache.py`](../tests/test_jev_g7_cache.py).
- [x] **[RAG-120]** Limpeza de dead code (opt): remoção de `llm_fallback.py` (`DynamicFallbackLLMManager`), `retriever.py` (`HybridRetriever`), CLI morto (`iniciar_chat()`/`main()`) e `api_key` duplicado em `chat.py`; remoção da dependência órfã `rank-bm25` de `requirements.txt` `[DONE]`.

### 1.3 Avaliação & Benchmark
- [x] **[RAG-110]** Criar script de benchmark `eval_merge.py` com conjunto de teste de perguntas complexas para medir taxa de alucinação.
- [x] **[RAG-111]** Avaliar migração futura de embeddings (`sentence-transformers/all-MiniLM-L6-v2` → `multilingual-e5-large`) para v2. Recomendação: migrar na v2 (melhor pt-BR, 1024 dims) com re-indexação completa do Pinecone — ver [`scripts/eval_embedding_migration.py`](../scripts/eval_embedding_migration.py).
- [x] **[RAG-114]** Verificação mecânica anti-alucinação (G2): `jev_check` pré-geração (base insuficiente ⇒ `NOT_FOUND_ANSWER`) e pós-geração (resposta contradita ⇒ substituída) `[DONE]` → [`backend/rag/jev_client.py`](../backend/rag/jev_client.py:213) + [`backend/rag/chat.py`](../backend/rag/chat.py:217).
- [x] **[RAG-118]** Analytics reativado (G6): `record_query()` canoniza o tema da query com `jev_choice` sob guardrail `JEV_MIN_CONFIDENCE = 0.9` e loga evento estruturado (`theme` + hash SHA-256 da query, sem texto cru); falha do Jev ⇒ tema `desconhecido` `[DONE]` → [`backend/api/analytics.py`](../backend/api/analytics.py:46) + [`tests/test_jev_g6_analytics.py`](../tests/test_jev_g6_analytics.py).
