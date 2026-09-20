# Jev — Mapa de Gaps de Eficiência & Economia (RAG)

> Varredura sênior de dados sobre o pipeline RAG. Foco: onde o **Jev**
> (`jev_ask` com `noul`/`choice`/`score` ou `jev_check`) reduz custo/latência
> **mantendo ou melhorando** a qualidade da resposta.
>
> Custo de referência: **~US$ 0,000012 por pergunta** `noul` (modelo
> `typesafe/jev-1.13` via OpenRouter, ~286 tokens de entrada). Latência
> adicional de ~0,5–1s por chamada.

---

## 1. Resumo executivo

O pipeline atual é **correto mas desperdiça tokens caros em pontos de decisão
baratos**. Toda a classificação de intenção é feita por regex e toda a
verificação anti-alucinação é feita **somente por prompt**. Isso significa que
o custo de uma decisão errada (rota errada, documento irrelevante, evidência
insuficiente) é pago na etapa mais cara: a síntese no LLM (Gemini pago).

O Jev resolve exatamente isso: é um modelo de **decisão calibrada** (retorna
`noul` 0–1, não prosa). Onde o pipeline precisa de um *gate* binário ou de um
*score* de confiança, o Jev substitui a síntese LLM por uma chamada ~100x mais
barata.

**Veredito: 6 gaps de alto valor + 1 gap de cache + 4 pontos de dead code.**

| # | Gap | Tipo Jev | Economia | Qualidade |
|---|-----|----------|----------|-----------|
| G1 | Roteamento semântico cego a paráfrases | `choice` | Alta (evita pipeline completo) | Alta (rota correta) |
| G2 | Anti-alucinação só por prompt | `check` | Média (evita geração inútil) | Alta (menos alucinação) |
| G3 | Rerank sem limiar de relevância | `noul` | Média (menos tokens no prompt) | Alta (menos ruído) |
| G4 | Web search dispara sempre em RAG | `noul` | Alta (corta DDGS+latência) | Neutra/alta |
| G5 | Conflito interno vs web não verificado | `check` | Baixa | Alta (hierarquia mecânica) |
| G6 | `record_query` é no-op (analytics morto) | `choice`/`noul` | Baixa | Alta (dados de produto) |
| G7 | Cache por string exata (sem dedup semântico) | `noul` | Alta (hit rate) | Neutra |

---

## 2. Gaps detalhados

### G1 — Roteamento semântico cego a paráfrases (prioridade máxima)

**Local:** [`SemanticRouter.route()`](backend/rag/semantic_router.py:61),
padrões [`_WEB_RE`](backend/rag/semantic_router.py:27),
[`_DOMAIN_RE`](backend/rag/semantic_router.py:33),
[`_DIRECT_RE`](backend/rag/semantic_router.py:43).

**Comportamento atual:** classificação determinística por regex sobre texto
normalizado. O `default` é [`return Route.RAG`](backend/rag/semantic_router.py:69).
Toda consulta que não casa nenhum padrão cai em RAG e dispara o pipeline
completo: Pinecone + DDGS + síntese Gemini.

**Problema:** paráfrases sem keyword do domínio ("quanto custa um deputado?",
"o que mudou na lei da transparência?") ou conversa casual que não casa
`_DIRECT_RE` são tratadas como pesquisa factual e pagam o custo máximo.

**Solução Jev:** usar `jev_ask` com `choice` (RAG/WEB/DIRECT) + confiança
calibrada **somente quando o regex não decidir com certeza**:

- Regex mantém decisão barata (custo zero) para os casos óbvios.
- Jev arbitra o caso ambíguo (default atual) a ~US$ 0,000012.
- **Guardrail de 90%:** o Jev só opera (decide a rota) quando devolve
  `confidence >= 0.9`. Abaixo disso, a decisão é delegada às nossas LLMs
  (decider via OpenRouter chat completions), que decidem prosseguir ou não.
- Jev ou decider indisponíveis → fallback `Route.RAG` (comportamento atual).

**Impacto:** elimina pipeline completo (Pinecone + DDGS 5s + Gemini) em
consultas fora do domínio. É o maior ganho de economia do mapa.

---

### G2 — Anti-alucinação apenas por prompt (verificação mecânica ausente)

**Local:** [`_build_synthesis_prompt()`](backend/rag/chat.py:213) e regra
[`BUSINESS_RULES.md` #2](.llm/BUSINESS_RULES.md:24). A instrução "não invente"
vive só no system prompt.

**Problema:** quando a base interna não tem evidência suficiente, o LLM ainda
sintetiza — e o prompt é o único freio. Nenhuma checagem mecânica confirma que
os documentos recuperados **de fato sustentam** a resposta.

**Solução Jev:** `jev_check` com `claim = pergunta` (ou resposta gerada) e
`evidence = documentos recuperados` antes de gerar:

- Evidência insuficiente (`noul` baixo) → responder "não encontrei na base"
  em vez de gastar a síntese Gemini.
- Pós-geração: `jev_check` da resposta contra as fontes antes do stream final.

**Impacto:** corte de gerações inúteis + redução objetiva de alucinação — o
requisito central de [`BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md:24).

---

### G3 — Rerank sem limiar de relevância

**Local:** [`PineconeRerank`](backend/rag/chat.py:65) com `top_n=5` fixo.

**Comportamento atual:** os 5 documentos rerankeados entram **todos** no prompt
de síntese, mesmo com score de relevância baixo. Não há corte.

**Problema:** documentos irrelevantes inflam o prompt (mais tokens pagos no
Gemini) e pioram a resposta (ruído competindo com a fonte boa).

**Solução Jev:** `noul` sobre cada documento top-k ("este trecho responde a
pergunta?"), mantendo só os acima de um limiar (ex.: `noul ≥ 0.5`). Como o
Jev lê contexto pequeno e custa ~US$ 0,000012, filtrar 5 docs custa ~US$
0,00006 — irrisório frente ao custo de token do Gemini.

**Impacto:** prompts enxutos, menos ruído, menos custo por síntese.

---

### G4 — Web search dispara em toda rota RAG

**Local:** [`MultiSourceAgentChain.invoke()`](backend/rag/chat.py:275) e
[`.stream()`](backend/rag/chat.py:305) chamam
[`_buscar_noticias_web()`](backend/rag/chat.py:137) sempre que
`route in (Route.RAG, Route.WEB)`, com timeout de 5s.

**Problema:** perguntas 100% factuais internas ("como o deputado X votou na
PEC Y") não precisam de DDGS, mas pagam a latência (até 5s) e o ruído web.

**Solução Jev:** `noul` "esta pergunta exige informação recente/notícias?"
antes de acionar DDGS. `noul < limiar` → pula web, vai só de Pinecone.

**Impacto:** corte de latência perceptível (5s → 0) e de ruído na síntese para
perguntas internas. Economia direta de tempo de execução no Cloud Run.

---

### G5 — Conflito interno vs web não verificado mecanicamente

**Local:** prompt de síntese hierárquica em
[`_build_synthesis_prompt()`](backend/rag/chat.py:213) — a base interna é a
fonte primária e a web é secundária, mas a resolução de conflito é delegada ao
LLM por instrução.

**Solução Jev:** `jev_check` "a fonte web contradiz a fonte base?" quando
ambas existirem. Conflito detectado → a síntese recebe flag explícita para
priorizar a base (ou responder citando a divergência).

**Impacto:** menor chance de a web contaminar a resposta factual; qualidade
alinhada a [`BUSINESS_RULES.md` #1](.llm/BUSINESS_RULES.md:10).

---

### G6 — Analytics morto (`record_query` no-op)

**Local:** [`record_query()`](backend/api/analytics.py:26) é um `pass`
marcado "(Obsoleto)", mas ainda é chamado via `background_tasks` em
[`main.py`](backend/api/main.py:268). A
[`BUSINESS_RULES.md` #6](.llm/BUSINESS_RULES.md:90) documenta fuzzy-match +
canonização por LLM que **não existe mais** (drift).

**Solução Jev:** canonizar/classificar a query com `choice`/`noul` barato em
vez de LLM de síntese, reativando métricas de produto (temas mais perguntados,
taxa de rota, abandono) por ~US$ 0,000012 por query.

**Impacto:** dados de produto de volta sem custo relevante; fecha o drift
entre docs e código.

---

### G7 — Cache por string exata (sem dedup semântico)

**Local:** [`RAGQueryCache._normalize_key()`](backend/rag/cache.py:13) usa
`{model}:{query_normalizado}` — dedup só por string idêntica.

**Problema:** "voto do deputado X na PEC Y" e "como o deputado X votou na PEC
Y" não compartilham cache, embora sejam a mesma pergunta. Cada paráfrase paga
o pipeline completo.

**Solução Jev:** `noul` de similaridade entre a query nova e chaves recentes
do cache (ou embedding barato). Hit semântico → reusa resposta.

**Impacto:** aumento de hit rate → menos chamadas Pinecone+Gemini repetidas.
Avaliar trade-off: exige comparar com embedding local (all-MiniLM) que já
existe no projeto e pode ser mais barato que o Jev aqui.

---

## 3. Dead code — candidatos a `horse-optimize` (não-Jev)

Estes não usam Jev; são limpeza de performance/simplicidade. **O skill
`horse-optimize` se aplica a este bloco** como tarefa de refatoração (não
executada aqui — modo horse-architect edita apenas `.md`):

| Item | Local | Ação |
|------|-------|------|
| `DynamicFallbackLLMManager` não importado | [`llm_fallback.py`](backend/rag/llm_fallback.py:13) | Remover módulo |
| `HybridRetriever` não usado (chat usa `PineconeHybridSearchRetriever`) | [`retriever.py`](backend/rag/retriever.py:11) | Remover ou reativar |
| CLI `iniciar_chat()`/`main()` morto | [`chat.py:379`](backend/rag/chat.py:379), [`chat.py:399`](backend/rag/chat.py:399) | Remover |
| `api_key` atribuído 2x (linhas 76 e 78) | [`chat.py:76`](backend/rag/chat.py:76), [`chat.py:78`](backend/rag/chat.py:78) | Remover duplicata |

---

## 4. Roadmap de implementação (ordem por ROI)

1. **G1** — roteamento Jev só no default ambíguo (menor mudança, maior
   economia). Regex continua soberano; Jev decide apenas com
   `confidence >= 0.9`; abaixo disso, decider LLM decide; fallback RAG.
2. **G4** — gate de web search com `noul` (1 chamada, corte de latência).
3. **G2** — gate de answerability pré-geração com `jev_check`.
4. **G3** — filtro de relevância pós-rerank com `noul`.
5. **G6** — reativar `record_query` com canonização Jev.
6. **G5** — checagem de conflito interno vs web.
7. **G7** — dedup semântico (comparar com embedding local antes).
8. **Dead code** — rodar `horse-optimize` para a limpeza da seção 3.

### Regras de integração obrigatórias

- Modelo fixo `typesafe/jev-1.13`; nunca `jev-latest` (não resolve no
  OpenRouter).
- **Guardrail de 90%:** toda integração Jev só opera com
  `confidence >= 0.9` (constante `JEV_MIN_CONFIDENCE`). Abaixo disso, a
  decisão é delegada às nossas LLMs (decider), nunca assumida pelo Jev.
- Toda chamada Jev com **timeout + retry** (regra #6 de segurança do
  `AGENTS.md`) e fallback para o comportamento atual se o Jev falhar — o
  pipeline **nunca pode quebrar** por indisponibilidade do Jev.
- Credencial via `OPENROUTER_API_KEY` (`.env`, gitignored), nunca hardcoded.
- Primeiro gate em `backend/api/guardrails.py` continua obrigatório e antes de
  qualquer chamada Jev (não mover a validação de injeção).

---

## 5. Conclusão

O Jev é **economicamente viável como camada de decisão**: US$ 0,000012 por
gate contra o custo de uma síntese Gemini completa (ordens de magnitude maior)
e contra 5s de DDGS. Os 6 gaps mapeados transformam decisões hoje feitas por
regex/prompt em decisões **calibradas e mecânicas**, com fallback seguro.

O skill `horse-optimize` **se aplica** apenas ao bloco de dead code (seção 3),
que é refatoração de simplicidade — não à integração Jev em si, que é
incremental e gateada por fallback.
