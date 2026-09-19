---
name: rag-loop
description: Executa ciclos automatizados de testes de conversa fluida (multiturn RAG), avaliando coerência contextual, fontes recuperadas e estabilidade do pipeline.
---

# Ciclo Automatizado de Testes RAG (Loop)

## Instructions

1. **Execução do Teste:** Rode o script ou framework de testes de conversa (ex: `pytest` ou runner de integração RAG).
2. **Validação Sequencial:** Simule ou valide as interações em cadeia (mínimo de 5 turnos), verificando se o modelo mantém o contexto e recupera as fontes corretamente sem alucinações.
3. **Análise de Desvios:** Identifique falhas de coerência ou erros de retorno nas fontes injetadas.
4. **Relatório:** Regista o status de sucesso/falha de cada turno para refinamento do prompt ou dos modelos.
