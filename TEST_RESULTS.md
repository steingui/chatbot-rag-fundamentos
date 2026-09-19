# Relatório de Testes e Validação de Pipeline & LLM

## 1. Validação CI/CD GitHub Actions
- **Status:** 100% Sucesso nas execuções manuais e agendadas.
- **Workflows Corrigidos:**
  - `Ingestão Diária - Fact Checking (RSS Multi-Agências)`
  - `Ingestão Diária - Querido Diário (Atos Municipais)`
  - `Ingestão Semanal - TSE DivulgaCandContas`
- **Causa Raiz Resolvida:** Inclusão de `langchain-community` via padronização `pip install -r requirements.txt`.

---

## 2. Validação de Modelos LLM (Google Gemini & OpenRouter)
- **Modelos Gratuitos e Pro Validados (API Google AI / OpenRouter):**
  1. `gemini-3.7-flash` (Modelo Principal)
  2. `gemini-3.6-flash` (Fallback Primário)
  3. `gemini-2.5-flash` / `gemini-flash-latest` (Fallback Secundário)
  4. `meta-llama/llama-3.3-70b-instruct:free` (OpenRouter Fallback)
  5. `deepseek/deepseek-r1-distill-llama-70b:free` (OpenRouter Fallback)

---

## 3. Teste Sequencial de Conversa (End-to-End)
- **Endpoint:** `POST https://chatbot-rag-api-1043919586992.southamerica-east1.run.app/chat/stream`
- **Segurança (SEC-005):** Validação de Origin/CORS OK.

### Sequência de Teste Executada:
1. **Turno 1 (`google/gemma-4-31b-it:free`):**
   - *Pergunta:* "Quais são as principais propostas sobre reforma tributária no Congresso?"
   - *Recuperação:* 7 fontes encontradas (Pinecone + DuckDuckGo).
   - *Resultado:* HTTP 200 OK (Stream gerado com sucesso).

2. **Turno 2 (`nvidia/nemotron-3.5-lightning:free`):**
   - *Pergunta:* "Quais são os impactos previstos para o imposto sobre consumo (IVA)?"
   - *Resultado:* HTTP 200 OK (Tratamento automático de rate-limit 429 com backoff concluído).

3. **Turno 3 (`minimax/minimax-m3:free`):**
   - *Pergunta:* "Resuma as principais conclusões levantadas nas etapas anteriores."
   - *Resultado:* HTTP 200 OK (Síntese unificada gerada).

---

## 4. Checkpoint de Validação Pós-Commits (`validate-commits`)

> **Adendo E2E produtivo:** os testes abaixo passaram a apontar para os ambientes
> reais de produção (Cloud Run + Firebase Hosting), em vez de mocks locais.

**Data:** Validação E2E dos últimos 5 commits em `main`.

### 4.1 Escopo inspecionado (`git log -n 5`)
| Commit | Descrição |
|--------|-----------|
| `2c92f68` | docs: documenta RAG-101 em arquitetura, regras de negócio e backlog |
| `a6a3d09` | feat: implementa roteamento semântico (RAG vs Web vs Direct) |
| `0cb39fd` | test: adiciona loop multiturn de coerência RAG com mocks determinísticos |
| `2c4bf23` | fix: suprime InconsistentVersionWarning e carrega PID scanner de forma lazy |
| `71529d0` | test: cobre contador de prompts e rewarded ads |

### 4.2 Arquivos alterados (resumo)
- [`backend/rag/semantic_router.py`](backend/rag/semantic_router.py:1) — novo roteador determinístico (regex + NFKD), sem custo de LLM.
- [`backend/rag/chat.py`](backend/rag/chat.py:252) — [`MultiSourceAgentChain.invoke()`](backend/rag/chat.py:252) e [`MultiSourceAgentChain.stream()`](backend/rag/chat.py:298) passaram a rotear por `SemanticRouter.route()`.
- [`backend/api/guardrails.py`](backend/api/guardrails.py:63) — [`_get_pid_scanner()`](backend/api/guardrails.py:63) lazy com `@lru_cache` + supressão de `InconsistentVersionWarning`.
- `frontend/src/store/useChatStore.ts` — contador de prompts guest + trava de rewarded ads (MON-602/MON-603).
- Testes novos: `tests/test_semantic_router.py`, `tests/test_rag_multiturn_loop.py`, `frontend/src/lib/__tests__/rewardedAds.test.ts`, `frontend/src/store/__tests__/useChatStore.test.ts`, `frontend/src/components/__tests__/RewardedAdModal.test.tsx`.

### 4.3 Resultados automatizados
| Suíte | Resultado |
|-------|-----------|
| Backend `pytest tests/ -q` | **50 passed** em 3.72s |
| Frontend `vitest run` | **16 passed** (3 arquivos) |
| **E2E produtivo backend** `RUN_E2E_PROD=1 pytest tests/test_e2e_production.py` | **6 passed** em 25.62s (Cloud Run real) |
| **E2E produtivo frontend** `RUN_E2E_PROD=1 vitest e2e.production.test.ts` | **4 passed** (Firebase Hosting + Cloud Run reais) |
| Smoke das rotas RAG/Web/Direct (uvicorn local) | OK, sem warnings/erros |

**Artefatos de E2E produtivo criados:**
- [`tests/test_e2e_production.py`](tests/test_e2e_production.py:1) — backend: healthcheck,
  rotas RAG/WEB/DIRECT, sugestões e streaming SSE contra `https://chatbot-rag-api-1043919586992.southamerica-east1.run.app`.
- [`frontend/src/__tests__/e2e.production.test.ts`](frontend/src/__tests__/e2e.production.test.ts:1) — frontend:
  app servido no Firebase Hosting (`https://rag-eleicoes.web.app`) + contrato `/api/v1/chat` e `/api/v1/chat/stream` em produção.

Ambos são **opt-in** (skipped por padrão para não rodar chamadas externas no CI);
habilitam via `RUN_E2E_PROD=1`. URLs sobrescrevíveis por `E2E_PROD_API_URL` e `E2E_PROD_FRONTEND_URL`.

### 4.4 Diagnóstico de regressões
- **Nenhuma regressão detetada.** As 3 rotas (`RAG`, `WEB`, `DIRECT`) respondem corretamente;
  `DIRECT` retorna `source_documents` vazio conforme especificado.
- `SemanticRouter` respeita a precedência: sinal de web vence domínio; domínio vence conversa casual.
- Guardrails mantêm bloqueio por regex (Camada 1) e PID Scanner (Camada 2) sem emitir o warning de versão do sklearn.

### 4.5 Pendências
- Nenhuma pendência de fix. Observação: as fontes recuperadas em `DIRECT` são intencionalmente vazias,
  portanto a UI deve exibir "sem fontes" nessa rota sem tratá-la como erro.
