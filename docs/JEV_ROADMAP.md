# Jev — Roadmap de Implementação

> **O quê** rotina a rotina, **por quê** faz diferença e **como** implementar.
> Complementa [`JEV_GAPS.md`](JEV_GAPS.md) (mapa de gaps) e
> [`JEV_ALERTING.md`](JEV_ALERTING.md) (observabilidade).
>
> Premissa: Jev é **camada de decisão**, não substituto da síntese. Cada gate
> custa ~US$ 0,000012 (modelo `typesafe/jev-1.13`) e **nunca quebra o pipeline**
> se falhar — sempre há fallback para o comportamento atual.

---

## 1. Camada de integração (pré-requisito de todas as rotinas)

Criar [`backend/rag/jev_client.py`](backend/rag/jev_client.py) — cliente fino
HTTP sobre o endpoint System One do OpenRouter. O caminho da Vercel AI Gateway
(`base_url="https://ai-gateway.vercel.sh"` e `AI_GATEWAY_API_KEY`) foi
descartado porque **não expõe** `/v1/systemone` (ver
[`docs/JEV_SETUP.md`](docs/JEV_SETUP.md:93)).

```python
JEV_ENDPOINT = "https://openrouter.ai/api/v1/systemone"
JEV_MODEL = "typesafe/jev-1.13"          # nunca "jev-latest" (404 no OpenRouter)
JEV_TIMEOUT = 5.0
```

API pública (todos os retornos `Optional`):

| Função | Assinatura | Retorno | Uso |
|--------|-----------|---------|-----|
| `jev_noul` | `(instructions, state) -> float \| None` | probabilidade 0–1 | gates binários |
| `jev_choice` | `(instructions, criteria, state) -> tuple[str, float] \| None` | `(rótulo, confiança)` | roteamento/canonização |
| `jev_check` | `(claim, evidence, state) -> float \| None` | consistência 0–1 | anti-alucinação/conflito |

**Contrato de robustez (obrigatório):**

- `httpx` com `timeout=JEV_TIMEOUT` + 1 retry em 5xx/timeout (regra #6 do
  [`AGENTS.md`](AGENTS.md)).
- Circuit breaker simples: 3 falhas consecutivas → abre por 60s e devolve
  `None` sem chamar a rede.
- **Guardrail de 90%:** o resultado do Jev só é usado quando
  `confidence >= JEV_MIN_CONFIDENCE` (0.9). Abaixo disso, a rotina delega a
  decisão às nossas LLMs (decider) — o Jev **nunca** decide com confiança
  baixa.
- **`None` ⇒ fallback silencioso** para o comportamento atual da rotina. O Jev
  é otimização, nunca dependência.
- Credencial via `OPENROUTER_API_KEY` (`.env`, gitignored). Nunca hardcoded.
- Log estruturado em toda chamada (contrato em
  [`JEV_ALERTING.md`](JEV_ALERTING.md)).

---

## 2. Rotinas (o quê / por quê / como)

### R1 — Roteamento semântico por fallback (MVP)

- **O quê:** classificar `RAG` / `WEB` / `DIRECT` **apenas quando o regex não
  decidir**. O [`SemanticRouter.route()`](backend/rag/semantic_router.py:126)
  hoje cai no default `Route.RAG` para qualquer paráfrase sem keyword.
- **Por quê:** consulta fora do domínio paga pipeline completo (Pinecone +
  DDGS 5s + Gemini). É o maior corte de custo do mapa.
- **Como:** implementado em [`SemanticRouter.route()`](backend/rag/semantic_router.py:126):
  1. regex soberano (custo zero) decide os casos óbvios;
  2. caso ambíguo → `jev_choice(...)` devolve `(choice, confidence)`;
  3. `confidence >= JEV_MIN_CONFIDENCE` (0.9) → usa `choice` do Jev;
  4. abaixo de 90% → delega ao decider LLM
     ([`_llm_decide()`](backend/rag/semantic_router.py:84));
  5. Jev/decider falharem → `Route.RAG`.
- **Fallback:** manter `Route.RAG` (comportamento atual).

### R2 — Gate de web search (MVP)

- **O quê:** decidir se a pergunta exige informação recente antes de chamar
  [`_buscar_noticias_web()`](backend/rag/chat.py:137).
- **Por quê:** perguntas factuais internas não precisam de DDGS; cada busca
  custa até 5s de latência e injeta ruído.
- **Como:**
  ```python
  if route == Route.RAG:
      needs_web = jev_client.jev_noul(
          instructions="Esta pergunta exige informação recente/notícias?",
          state={"pergunta": question},
      )
      if needs_web is not None and needs_web < 0.5:
          route = Route.RAG  # sem web
      else:
          web_context, web_sources = _buscar_noticias_web(question, session_id)
  ```
- **Fallback:** `None` ⇒ buscar web como hoje.

### R3 — Gate de answerability (Fase 2)

- **O quê:** verificar se os documentos recuperados sustentam a pergunta antes
  da síntese em [`MultiSourceAgentChain.invoke()`](backend/rag/chat.py:252).
- **Por quê:** anti-alucinação hoje é só prompt
  ([`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md:24)); quando não há evidência, o
  LLM ainda gasta síntese.
- **Como:**
  ```python
  support = jev_client.jev_check(
      claim=question,
      evidence=pinecone_context,
      state={"pergunta": question},
  )
  if support is not None and support < 0.5:
      return {"answer": "Não encontrei informação suficiente na base interna.",
              "source_documents": sources}
  ```
- **Fallback:** `None` ⇒ gerar normalmente.

### R4 — Limiar de relevância pós-rerank (Fase 2)

- **O quê:** filtrar os 5 docs do [`PineconeRerank`](backend/rag/chat.py:65) por
  relevância real.
- **Por quê:** doc irrelevante infla o prompt Gemini e piora a resposta.
- **Como:** `jev_noul("Este trecho responde à pergunta?", state=...)` por doc;
  mantém só `noul >= 0.5`. Custo de filtrar 5 docs ≈ US$ 0,00006 — irrisório.
- **Fallback:** manter `top_n=5`.

### R5 — Detecção de conflito interno vs web (Fase 3)

- **O quê:** quando há `pinecone_context` e `web_context`, checar contradição.
- **Por quê:** preserva a hierarquia da fonte primária de forma mecânica, não
  por instrução de prompt ([`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md:10)).
- **Como:** `jev_check(claim="A fonte web contradiz a fonte base?",
  evidence=web_context + base, ...)`. Conflito ⇒ flag explícita no prompt de
  síntese para priorizar a base.
- **Fallback:** síntese com instrução hierárquica atual.

### R6 — Canonização de query para analytics (Fase 3)

- **O quê:** reativar [`record_query()`](backend/api/analytics.py:26), hoje
  `pass`, canonizando a query com Jev.
- **Por quê:** fecha o drift com [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md:90)
  e devolve métricas de produto (temas, rotas, abandono) a ~US$ 0,000012/query.
- **Como:** `jev_choice` para tema/categoria + persistência no Firestore.
- **Fallback:** manter no-op.

### R7 — Dedup semântico de cache (Avaliar)

- **O quê:** [`RAGQueryCache._normalize_key()`](backend/rag/cache.py:13) deduplica
  só por string exata.
- **Por quê:** paráfrases pagam o pipeline de novo.
- **Como:** comparar `jev_noul` de similaridade contra chaves recentes **vs**
  embedding local (all-MiniLM já existe). **Decidir por benchmark** — o
  embedding local pode ser mais barato e não depende de rede.
- **Fallback:** chave exata atual.

---

## 3. Fases de entrega

| Fase | Escopo | Critério de aceite |
|------|--------|--------------------|
| **MVP** | `jev_client.py` + R1 + R2 + logging/alerting | Testes unitários com Jev mockado; teste de fallback (Jev fora ⇒ pipeline idêntico); métrica de falha visível |
| **Fase 2** | R3 + R4 | Menor taxa de resposta "não encontrei" sem piorar recall; prompts ≤ N tokens |
| **Fase 3** | R5 + R6 | Conflito flagrado mecanicamente; analytics populado |
| **Avaliar** | R7 | Benchmark hit rate vs custo (Jev × embedding local) |

---

## 4. Regras de implementação

1. **SDD**: escrever o teste (gate com Jev mockado → falha), implementar o gate,
   passar o teste. Mockar `jev_client` em todos os testes que não são de
   integração.
2. **Diff-only**: cada rotina toca só a função necessária; nunca reescrever
   [`chat.py`](backend/rag/chat.py) inteiro.
3. **Tipagem**: type hints em todas as funções novas (`float | None`, `dict`).
4. **Timeout + retry**: obrigatórios (regra #6 de [`AGENTS.md`](AGENTS.md)).
5. **Guardrail de 90%**: `confidence < JEV_MIN_CONFIDENCE` (0.9) ⇒ delegar a
   decisão às nossas LLMs (decider); nunca agir com a escolha do Jev abaixo
   desse limiar.
6. **Guardrails primeiro**: [`validate_and_sanitize_query()`](backend/api/guardrails.py:77)
   continua antes de qualquer gate Jev.
7. **Budget**: contador de chamadas Jev por instância + teto diário configurável
   (`JEV_DAILY_BUDGET`) para nunca exceder o custo previsto.

---

## 5. Aceite de custo

| Rotina | Chamadas/query (pior caso) | Custo/query |
|--------|---------------------------|-------------|
| R1 | 1 | ~US$ 0,000012 |
| R2 | 1 | ~US$ 0,000012 |
| R3 | 1 | ~US$ 0,000012 |
| R4 | 5 | ~US$ 0,00006 |
| R5 | 1 | ~US$ 0,000012 |
| R6 | 1 | ~US$ 0,000012 |

MVP (R1+R2): ~US$ 0,000024/query. Com US$ 10 de crédito ⇒ ~416 mil queries
antes de esgotar — desprezível frente ao custo de uma síntese Gemini.
