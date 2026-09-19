---
name: validate-commits
description: Valida a integridade E2E de commits recentes, interage solicitando logs/prints para detetar regressões, gera apontamentos de fix e atualiza os markdowns de checkpoint.
---

# Validação Pós-Commits e Controlo de Regressões

## Instructions

1. **Inspeção de Alterações:** Execute `git log -n 5 --oneline` e `git diff HEAD~5` para mapear o escopo técnico modificado recentemente.
2. **Investigação Interativa:** Faça perguntas objetivas e sugestões de validação ao utilizador, solicitando explicitamente logs de execução, prints ou testes de comportamento E2E.
3. **Diagnóstico de Regressões:** Cruzar os feedbacks recolhidos com o código alterado para isolar eventuais quebras no pipeline ou na interface.
4. **Apontamentos de Fix e Checkpoints:** Caso existam regressões, produza um contexto técnico estruturado para o *fix* e atualize os ficheiros Markdown de *checkpoint* do projeto com o diagnóstico e pendências detetadas.
