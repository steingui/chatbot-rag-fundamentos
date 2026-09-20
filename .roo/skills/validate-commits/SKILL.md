---
name: validate-commits
description: Valida a integridade E2E de commits recentes, cruza feedback com o diff usando gate Jev para detetar regressões, gera apontamentos de fix e atualiza os markdowns de checkpoint.
---

# Validação Pós-Commits e Controlo de Regressões

## Instructions

1. **Inspeção de Alterações:** Execute `git log -n 5 --oneline` e `git diff HEAD~5` para mapear o escopo técnico modificado recentemente.
2. **Investigação Interativa:** Faça perguntas objetivas e sugestões de validação ao utilizador, solicitando explicitamente logs de execução, prints ou testes de comportamento E2E.
3. **Diagnóstico de Regressões com Gate Jev (MCP `jevcore`):** Para cada feedback recolhido, chame `jev_check` com:
   - `claim`: `"O feedback do usuário indica uma regressão causada pelas alterações recentes?"`
   - `evidence`: trecho relevante do `git diff` + feedback/logs fornecidos.
   - Resultado `supported` ⇒ tratar como regressão provável e isolar o arquivo/linha responsável.
   - Resultado `contradicted` ou `insufficient` ⇒ descartar regressão para aquele feedback.
   - **Fallback:** Jev indisponível (`None`, erro ou timeout) ⇒ manter o cruzamento manual do passo 3 atual. O Jev nunca bloqueia a validação.
4. **Auditoria de Drift Semântico doc ↔ código (H1):** Para as regras/contratos de `.llm/` tocados no diff (top-N, máx. 10 pares), chame `jev_check` com:
   - `claim`: a frase do documento que afirma um comportamento;
   - `evidence`: o trecho de código correspondente lido no momento.
   - Resultado `contradicted` ⇒ **drift** (o doc afirma algo que o código não faz): gerar apontamento de fix no `.llm/` correspondente.
   - Resultado `insufficient` ⇒ evidência fraca: sinalizar para revisão manual.
   - Resultado `supported` ⇒ doc e código alinhados.
   - **Fallback:** Jev indisponível (`None`, erro ou timeout) ⇒ manter a auditoria manual atual. O Jev otimiza, nunca bloqueia.
5. **Apontamentos de Fix e Checkpoints:** Caso existam regressões (passo 3) ou drift (passo 4), produza um contexto técnico estruturado para o *fix* e atualize os ficheiros Markdown de *checkpoint* do projeto com o diagnóstico e pendências detetadas.
