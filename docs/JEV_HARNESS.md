# Jev — Melhoria do Harness de Contexto da LLM

> **Status: H1 implementado** via SDD-cycle (teste de aceite →
> [`test_harness_links.py`](tests/test_harness_links.py:132) falhou → passo 4
> adicionado ao skill [`validate-commits`](.roo/skills/validate-commits/SKILL.md:18)
> → teste passou). H2 permanece opcional/adiado.

> Pergunta: **podemos melhorar o harness na codebase com Jev?**
>
> Resposta curta: **parcialmente, sim** — mas só na camada de *drift semântico*.
> As invariantes determinísticas do harness **não** devem receber Jev; o Jev
> entra onde hoje o harness é cego: doc `.llm/` que descreve comportamento que
> o código **já não tem**.

---

## 1. O que é o harness hoje

O harness de contexto da LLM é o conjunto de invariantes que garante que a
codebase expõe à LLM apenas o contexto necessário e sem fatos obsoletos.
A fonte executável é [`test_harness_links.py`](tests/test_harness_links.py:1),
que valida:

| Invariante | Tipo | Local |
|------------|------|-------|
| P0-1 | Bootstrap enxuto na raiz (`AGENTS.md`, `README.md`, `CLAUDE.md`) | [`test_root_md_are_only_bootstrap()`](tests/test_harness_links.py:66) |
| P0-2 | Sem referência obsoleta (`render.yaml`, endpoint/modelo hardcoded) | [`test_no_stale_render_reference()`](tests/test_harness_links.py:74) |
| P0-3 | Artefatos pesados fora da raiz | [`test_heavy_artifacts_not_in_root()`](tests/test_harness_links.py:58) |
| P0-4 | `.llm/MANIFEST.md` indexa todos os docs | [`test_manifest_exists_and_indexes_all_llm_docs()`](tests/test_harness_links.py:100) |
| P1-1 | Skills de provider são stubs | [`test_provider_skills_are_stubs()`](tests/test_harness_links.py:108) |
| P1-4 | Roteamento único via MANIFEST | [`test_agents_md_routes_via_manifest()`](tests/test_harness_links.py:125) |

**Limitação estrutural:** todas essas invariantes são **sintáticas** (existência
de arquivo, regex, contagem de linhas). Nenhuma verifica se o **conteúdo** de um
doc `.llm/` ainda descreve o código de verdade.

---

## 2. O gap que o Jev cobre: drift semântico doc ↔ código

O exemplo canônico já foi encontrado manualmente no
[`JEV_GAPS.md`](docs/JEV_GAPS.md:146) (G6):

> [`BUSINESS_RULES.md` #6](.llm/BUSINESS_RULES.md:90) documenta fuzzy-match +
> canonização por LLM que **não existe mais** — o
> [`record_query()`](backend/api/analytics.py:26) é `pass`.

Nenhuma invariante atual pegaria isso: o arquivo existe, está indexado no
MANIFEST e não contém `render.yaml`. O drift é **semântico** — exige comparar a
afirmação do doc com a realidade do código. Essa comparação é exatamente o que
`jev_check` faz: `claim` = afirmação do doc, `evidence` = trecho de código.

---

## 3. Matriz de decisão: onde Jev entra e onde não entra

| Camada do harness | Jev se aplica? | Justificativa |
|-------------------|----------------|---------------|
| Invariantes P0-x/P1-x (arquivo, regex, linha) | ❌ Não | Fluxo determinístico; Jev adicionaria latência sem melhorar a decisão (mesma regra da seção 3 deste documento) |
| **Drift semântico doc ↔ código (novo)** | ✅ **Sim** | `jev_check` compara afirmação × evidência; é a única forma de pegar doc stale sem LLM de síntese |
| Validação do roteamento do MANIFEST (custo × suficiência) | ⚠️ Marginal | `jev_choice`/`jev_noul` pode auditar se a tabela roteia uma tarefa para o doc mais barato que responde — útil como auditoria periódica, não por task |
| Contagem de tokens (`bytes/4` do MANIFEST) | ❌ Não | Aritmética determinística |

**Conclusão:** o harness ganha **uma** camada nova (H1, abaixo) com Jev. As
demais camadas permanecem determinísticas — o teste
[`test_harness_links.py`](tests/test_harness_links.py:1) continua sendo o gate
de CI e o Jev nunca o substitui.

---

## 4. Proposta de implementação

### H1 — Auditoria de drift semântico com `jev_check` (valor alto)

Fluxo (a executar como skill ou como extensão do
[`validate-commits`](.roo/skills/validate-commits/SKILL.md:1)):

1. Para cada afirmação de comportamento em `.llm/` (ex.: regra de negócio,
   contrato de endpoint, assinatura de função descrita), extrair:
   - `claim` = a frase do doc que afirma um comportamento;
   - `evidence` = o trecho de código correspondente (lido no momento).
2. `jev_check(claim, evidence)`:
   - `contradicted` → **drift** — o doc afirma algo que o código não faz;
   - `insufficient` → evidência fraca (doc vago ou código ausente) — sinalizar
     para revisão manual;
   - `supported` → doc e código alinhados.
3. Gerar relatório priorizado e abrir fix (atualizar o `.llm/` no mesmo commit,
   conforme regra 4 do [`MANIFEST.md`](.llm/MANIFEST.md:25)).

**Fallback:** Jev indisponível (`None`, erro ou timeout) ⇒ manter a auditoria
manual atual (o próprio G6 foi achado manualmente). O Jev otimiza, nunca bloqueia.

**Custo:** ~US$ 0,000012 por par (claim, evidence). Auditar ~20 regras de
negócio/contratos custa ~US$ 0,00024 — desprezível frente ao custo de deixar um
doc stale guiar uma decisão errada do agente.

### H2 — Auditoria de roteamento do MANIFEST (valor marginal, opcional)

`jev_choice` sobre uma amostra de tarefas reais: "qual documento do MANIFEST é
o mínimo suficiente para esta tarefa?" vs o que a tabela atual roteia. Divergência
→ ajustar a tabela. **Adiar:** o ganho é pequeno e a tabela é estável; implementar
só se a auditoria H1 revelar roteamento incorreto recorrente.

### Não fazer

- Não trocar `test_harness_links.py` por Jev — as invariantes sintáticas são
  baratas, determinísticas e já cobrem P0/P1.
- Não criar `jev_client.py` no backend para isso — esta auditoria roda no
  **tempo do agente** (MCP `jevcore`), não no runtime do Cloud Run. O
  [`jev_client.py`](backend/rag/jev_client.py) do
  [`JEV_ROADMAP.md`](docs/JEV_ROADMAP.md:15) é para gates de runtime, outro
  escopo.

---

## 5. Recomendação

1. **Estender** o skill [`validate-commits`](.roo/skills/validate-commits/SKILL.md:1)
   com um passo "drift semântico" usando `jev_check`, limitado ao top-N de
   regras/contratos alterados no diff (budget, sem auditar o repo inteiro).
2. **Manter** [`test_harness_links.py`](tests/test_harness_links.py:1) intacto
   como gate determinístico de CI.
3. **Rodar** a auditoria H1 de forma manual/periódica (não por commit) até
   calibrar o limiar de `contradicted` que dispara fix automático.

Veredito final: **sim, o harness melhora com Jev — adicionando uma camada de
drift semântico que hoje não existe, sem tocar nas invariantes determinísticas
que já funcionam.**

---

## 6. Resultado da primeira auditoria H1 (drift semântico doc ↔ código)

Executada em `fix/gcp-auth-cloud-run-publico` com `jev_check` (MCP `jevcore`)
sobre 10 pares `(claim, evidence)` extraídos de `.llm/`. Custo total da rodada:
~US$ 0,00018.

| # | Claim auditada | Veredito | Ação |
|---|----------------|----------|------|
| 1 | [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md) — `record_query` faz fuzzy-match + canonização LLM | `contradicted` (0.97) | **Drift corrigido**: doc reescrito para refletir `record_query()` no-op |
| 2 | [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md) — retriever ativo é `HybridRetriever` Dense+BM25/RRF | `contradicted` (0.94) | **Drift corrigido**: doc passa a descrever `PineconeHybridSearchRetriever` + `PineconeRerank` |
| 3 | [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md) — roteamento determinístico, sem custo de LLM | `contradicted` (0.95) | **Drift corrigido**: doc passa a descrever Jev/decider no default ambíguo |
| 4 | [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md) — regex de injeção com 11 padrões | `contradicted` (0.95) | **Drift corrigido**: doc passa a descrever ~30 padrões + scanner PID |
| 5 | [`API_CONTRACT.md`](.llm/API_CONTRACT.md) — `/suggestions` retorna top 8 por contagem | `contradicted` (0.97) | **Drift corrigido**: doc passa a descrever prompts curados aleatórios, `count=0` |
| 6 | [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md) — seeds de 8 sugestões no SQLite (`init_analytics_db`) | `contradicted` (0.92) | **Drift corrigido**: doc remove referência a SQLite/seeds |
| 7 | [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md) — `source_documents[]` + `SourceBadges` clicáveis | `contradicted` (0.74, sufficient 0.29) | **Insufficient** (evidência fraca): manter — campo existe e `SourceBadges.tsx` renderiza; revisar redação do contrato |
| 8 | [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md) — RAGQueryCache TTL/max/chave/eviction | `insufficient` (sufficient 0.63) | **Revisão manual**: eviction é LRU via `cachetools.TTLCache`, não "entry mais antigo" literal |
| 9 | [`API_CONTRACT.md`](.llm/API_CONTRACT.md) — rate limits 60/30/30 por IP | `supported` (0.73) | Alinhado |
| 10 | [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md) — hierarquia de confiança base interna > web | `supported` (0.97) | Alinhado |

**Correções aplicadas** no mesmo commit (regra 4 do
[`MANIFEST.md`](.llm/MANIFEST.md:25)): [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md)
(seções Guardrails, Analytics, Roteamento, Retriever) e
[`API_CONTRACT.md`](.llm/API_CONTRACT.md:20) (`/suggestions`).

**Limiar observado:** `contradicted` com `contradicts >= 0.9` foi confiável para
disparar fix automático; `contradicted` com `sufficient < 0.5` (claim 7) deve ser
tratado como evidência fraca → revisão manual, não fix automático.
