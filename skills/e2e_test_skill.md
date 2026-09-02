# Skill: Execução de Teste E2E e Abertura Autônoma de Issues

Esta skill instrui um Agente Tester a simular a interação de uma determinada Persona no chatbot RAG político e reportar bugs encontrados no repositório GitHub.

---

## 1. Protocolo de Interação de Teste

1. **Leitura da Persona**:
   - Carregar as características, metas e critérios de falha do arquivo em `personas/<nome_persona>.md`.
2. **Execução de Consulta (Via API ou Frontend)**:
   - **Endpoint local/remoto**: `POST https://chatbot-rag-api-1043919586992.southamerica-east1.run.app/chat`
   - **Payload**:
     ```json
     {
       "message": "<PROMPT_DA_PERSONA>",
       "session_id": "persona_test_<TIMESTAMP>",
       "model": "gemini-1.5-flash"
     }
     ```
3. **Avaliação da Resposta (Checklist de Validação)**:
   - [ ] A resposta atendeu ao objetivo da persona sem violar jargões/formato?
   - [ ] Existem reticências (`...`) ou truncamentos indesejados?
   - [ ] As fontes (`sources`) contêm URLs válidas e sem parâmetros sujos?
   - [ ] O modelo respeitou os guardrails de segurança (se a persona for adversarial)?
   - [ ] O tempo de resposta ficou abaixo do timeout limite?

---

## 2. Protocolo de Abertura de Issue via GitHub CLI (`gh`)

Caso ocorra qualquer falha nos critérios acima, o agente DEVE reportar o bug imediatamente via `gh issue create`:

```bash
gh issue create \
  --title "[QA Persona: $PERSONA_NAME] $DESCRICAO_CURTA_BUG" \
  --label "bug,qa-automation" \
  --body "## Relatório de Teste de Persona

- **Persona**: $PERSONA_NAME
- **Prompt Enviado**: \`$PROMPT\`
- **Modelo Utilizado**: \`$MODEL\`

### Falha Detectada
$DESCRICAO_DETALHADA_DO_ERRO

### Resposta Obtida
\`\`\`text
$RESPOSTA_OBTIDA
\`\`\`

### Comportamento Esperado
$COMPORTAMENTO_ESPERADO"
```
