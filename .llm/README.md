# .llm/ — Documentação de Engenharia Reversa para LLMs

Esta pasta contém a **single source of truth** sobre a codebase do **RAG Político**.
Qualquer LLM (Claude, GPT, Gemini, Copilot, etc.) deve ler estes arquivos antes de propor alterações.

## Índice de Documentos

| Arquivo | Conteúdo |
|---------|----------|
| `ARCHITECTURE.md` | Visão geral da arquitetura, camadas, fluxo de dados e deploy |
| `BUSINESS_RULES.md` | Regras de negócio, domínio, invariantes e validações |
| `API_CONTRACT.md` | Contratos HTTP (endpoints, DTOs, SSE, rate limits) |
| `DATA_MODEL.md` | Modelos de dados (frontend types, Pydantic models, SQLite schema) |
| `COMPONENT_MAP.md` | Mapa de componentes React + store Zustand |
| `DESIGN_SYSTEM.md` | Tokens de design, paleta, tipografia e convenções visuais |
| `DEPENDENCY_GRAPH.md` | Grafo de dependências internas e externas (Python + Node) |
| `CONVENTIONS.md` | Convenções de código, naming, commit, branch e testes |

## Como Usar

1. **Antes de codificar**: Leia `ARCHITECTURE.md` + o arquivo relevante ao domínio da tarefa.
2. **Antes de alterar API**: Leia `API_CONTRACT.md` + `DATA_MODEL.md`.
3. **Antes de alterar UI**: Leia `COMPONENT_MAP.md` + `DESIGN_SYSTEM.md`.
4. **Antes de adicionar dependência**: Leia `DEPENDENCY_GRAPH.md`.

## Manutenção

Sempre que uma alteração estrutural for feita na codebase, o arquivo `.llm/` correspondente
**deve ser atualizado no mesmo commit**. Isso garante que a documentação nunca fique stale.
