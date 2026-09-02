# 🧠 Backlog 01: RAG, Modelos de IA e Mitigação de Alucinações

> **Objetivo:** Garantir respostas precisas, sem alucinações, com baixo custo e alta resiliência de LLMs.

---

## 🎯 Tarefas & Histórias de Usuário

### 1.1 Roteamento Semântico & Fallbacks (Multi-LLM)
- [ ] **[RAG-101]** Implementar roteamento semântico (`SemanticRouter`) para classificar a intenção do usuário antes de acionar ferramentas (RAG vs Web vs Direct LLM).
- [ ] **[RAG-102]** Migrar fallback de OpenRouter Free para Google AI Studio (`gemini-3.7-flash`) como LLM primária.
- [ ] **[RAG-103]** Integrar Groq (`llama-3.3-70b`) como LLM Fallback 1 para absorção de rate-limits (HTTP 429).
- [ ] **[RAG-104]** Integrar DeepSeek V4 Flash via API direta como Fallback 2 de baixíssimo custo.
- [ ] **[RAG-105]** Configurar transição automática para Gemini 3.7 Paid Tier em picos de tráfego.

### 1.2 Qualidade de Contexto & Reranking
- [x] **[RAG-106]** Integrar Pinecone Hybrid Search (Vetor + BM25 léxico) para termos exatos e nomes de parlamentares.
- [x] **[RAG-107]** Configurar `bge-reranker-v2-m3` nativo no Pinecone para ordenação de relevância pós-recuperação.
- [ ] **[RAG-108]** Ajustar prompt de síntese hierárquica isolando contexto factual interno de resultados web secundários.
- [ ] **[RAG-109]** Implementar janela de contexto dinâmico baseada em contagem exata de tokens para evitar perda de histórico recente.

### 1.3 Avaliação & Benchmark
- [ ] **[RAG-110]** Criar script de benchmark `eval_merge.py` com conjunto de teste de perguntas complexas para medir taxa de alucinação.
- [ ] **[RAG-111]** Avaliar migração futura de embeddings (`sentence-transformers/all-MiniLM-L6-v2` → `multilingual-e5-large`) para v2.
