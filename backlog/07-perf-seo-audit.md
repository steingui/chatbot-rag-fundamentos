# 🚀 Backlog 07: Auditoria Perf/SEO — Issue #13

> **Origem:** https://github.com/steingui/chatbot-rag-fundamentos/issues/13
> **URL auditada:** https://rag-eleicoes.web.app/ · **Data:** 2026-09-20
> **Resultado:** 7 findings (0 critical, 2 high, 3 medium, 2 low).

---

## ✅ Findings implementados (SDD — commit desta entrega)

- [x] **[PERF-01] [DONE]** Fontes Google Fonts sem `@import` render-blocking: removido o `@import` de [`frontend/src/index.css`](../frontend/src/index.css:1) e carregada a folha via `<link rel="preconnect">` + `<link rel="stylesheet" media="print" onload="this.media='all'">` em [`frontend/index.html`](../frontend/index.html:16). *(finding 1 — HIGH)*
- [x] **[PERF-02] [DONE]** Eventos de progresso no SSE: [`MultiSourceAgentChain.stream()`](../backend/rag/chat.py:429) agora emite `{type:"stage", stage:"retrieving|generating|done"}`; [`chat_stream`](../backend/api/main.py:283) os repassa e [`useChatStore.sendMessageStream()`](../frontend/src/store/useChatStore.ts:522) atualiza `streamStage`, renderizado por [`stageLabel()`](../frontend/src/store/useChatStore.ts:24) em [`MessageList.tsx`](../frontend/src/components/MessageList.tsx:129). *(finding 2 — HIGH, parte "progresso no SSE")*
- [x] **[SEO-01] [DONE]** Social cards com imagem: `og:image` + `og:image:width/height/alt` + `twitter:image` e asset [`frontend/public/og-image.svg`](../frontend/public/og-image.svg:1). *(finding 3 — MEDIUM)*
- [x] **[SEO-02] [DONE]** JSON-LD `WebSite` com `potentialAction SearchAction` em [`frontend/index.html`](../frontend/index.html:49). *(finding 5 — MEDIUM)*
- [x] **[SEO-03] [DONE]** `twitter:card=summary_large_image` + `<meta name="robots" content="index,follow">`. *(finding 7 — LOW)*
- [x] **[MON-604] [DONE]** Ad-gate menos intrusivo: [`RewardedAdModal.tsx`](../frontend/src/components/RewardedAdModal.tsx:10) troca o modal interruptivo por banner inline e antecipa os prompts restantes do lote via [`promptsRemainingInBatch()`](../frontend/src/store/useChatStore.ts:16). *(finding 4 — MEDIUM)*
- [x] **[UX-01] [DONE]** Restaurou as ações de contexto no novo layout: painel "Ações de contexto" em [`SessionSidebar.tsx`](../frontend/src/components/SessionSidebar.tsx:105) com **Resumir chat** ([`summarizeConversation()`](../frontend/src/store/useChatStore.ts:311), prompt canônico [`SUMMARY_PROMPT`](../frontend/src/store/useChatStore.ts:13)), **Limpar contexto** ([`clearActiveSession()`](../frontend/src/store/useChatStore.ts:319)) e **Limpar tudo** ([`clearAllSessions()`](../frontend/src/store/useChatStore.ts:338)). Cobertura em [`DashboardShell.test.tsx`](../frontend/src/components/__tests__/DashboardShell.test.tsx:38).

## ⏳ Follow-ups pendentes

- [x] **[PERF-03] [DONE]** Paralelizou recuperação Pinecone + busca web DDGS no stream via [`_fetch_sources_parallel()`](../backend/rag/chat.py:430), sobrepondo o I/O dominante para reduzir a 1ª resposta (~58s → alvo <10s). Teste de regressão em [`tests/test_stream_parallel_fetch.py`](../tests/test_stream_parallel_fetch.py:1). *(issue #14, finding 1 — HIGH)*
- [x] **[PERF-05] [DONE]** Fallback de continuação quando o stream falha NO MEIO (finding 1 CRITICAL da issue #16): [`MultiSourceAgentChain.stream()`](../backend/rag/chat.py:457) agora tenta `llm.invoke()` (com `with_fallbacks`, trocando de modelo) e emite a continuação sem duplicar tokens via [`_continuation()`](../backend/rag/chat.py:527); o aviso de instabilidade só aparece se o fallback também falhar. Testes em [`tests/test_stream_midstream_fallback.py`](../tests/test_stream_midstream_fallback.py:1).
- [x] **[PERF-06] [DONE]** Instrumentação de latência do stream (finding 2 HIGH da issue #16): log JSON estruturado `chat_stream_latency` com `retrieval_ms`, `ttfb_ms` (1º token) e `total_ms` para isolar geração vs. recuperação nos ~21s observados. Teste em [`tests/test_stream_latency_log.py`](../tests/test_stream_latency_log.py:1).
- [ ] **[PERF-04]** Identificar origem do console warning "Deprecated API for given entry type" (SDK de terceiros — provável Firebase Auth) e atualizar a dependência. *(issue #14, finding 5 — LOW)*
