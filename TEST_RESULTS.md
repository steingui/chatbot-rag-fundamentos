# Relatório de Testes e Validação de Pipeline & LLM

## 1. Validação CI/CD GitHub Actions
- **Status:** 100% Sucesso nas execuções manuais e agendadas.
- **Workflows Corrigidos:**
  - `Ingestão Diária - Fact Checking (RSS Multi-Agências)`
  - `Ingestão Diária - Querido Diário (Atos Municipais)`
  - `Ingestão Semanal - TSE DivulgaCandContas`
- **Causa Raiz Resolvida:** Inclusão de `langchain-community` via padronização `pip install -r requirements.txt`.

---

## 2. Validação de Modelos LLM (OpenRouter)
- **Erros Solucionados:** Eliminação de HTTP 404 causados por modelos descontinuados (`nemotron-3-nano:free`, `gemini-2.0-flash-exp:free`).
- **Modelos Gratuitos Validados em Tempo Real (API OpenRouter):**
  1. `google/gemma-4-31b-it:free` (Modelo Principal)
  2. `nvidia/nemotron-3.5-lightning:free` (Fallback 1)
  3. `minimax/minimax-m3:free` (Fallback 2)
  4. `nvidia/nemotron-3-super-120b-a12b:free` (Alternativo)

---

## 3. Teste Sequencial de Conversa (End-to-End)
- **Endpoint:** `POST https://chatbot-rag-api-q2k5.onrender.com/chat/stream`
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
