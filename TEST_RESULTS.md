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
