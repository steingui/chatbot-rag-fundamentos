---
name: rag-loop
description: Executa ciclos automatizados de testes de conversa fluida (multiturn RAG), avaliando coerência contextual, fontes recuperadas e estabilidade do pipeline com gate Jev calibrado.
---

# Ciclo Automatizado de Testes RAG (Loop)

## Instructions

1. **Execução do Teste:** Rode o script ou framework de testes de conversa (ex: `pytest` ou runner de integração RAG).
2. **Validação Sequencial:** Simule ou valide as interações em cadeia (mínimo de 5 turnos), verificando se o modelo mantém o contexto e recupera as fontes corretamente sem alucinações.
3. **Gate Jev por turno** (ferramentas `jev_check` e `jev_ask` do MCP `jevcore`):
   - **Coerência contextual:** `jev_check(claim="A resposta do turno N mantém coerência com o contexto dos turnos anteriores?", evidence=histórico_dos_turnos_anteriores)`.
   - **Sustentação por fonte:** `jev_ask` com `type: "noul"` e instructions `"As fontes recuperadas sustentam a resposta do turno?"`, usando `state` com pergunta, resposta e fontes do turno.
   - Turno com `jev_check` indicando `contradicted` ou `noul < 0.5` → marcar o turno como `FAIL`.
   - **Fallback:** se o Jev estiver indisponível (`None`, erro ou timeout), manter o julgamento manual do passo 2. O Jev otimiza, nunca bloqueia o loop.
4. **Análise de Desvios:** Identifique falhas de coerência ou erros de retorno nas fontes injetadas, priorizando os turnos com `FAIL` do passo 3.
5. **Relatório:** Registre o status de sucesso/falha de cada turno (com score Jev quando disponível) para refinamento do prompt ou dos modelos.
