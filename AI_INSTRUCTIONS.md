# Diretrizes para IA (Engenharia e Arquitetura)

## ⚠️ Leia primeiro: `.llm/`

Antes de qualquer alteração, **leia os documentos em `.llm/`** que contêm
engenharia reversa detalhada de toda a codebase:

| Arquivo | Quando ler |
|---------|-----------|
| [`.llm/ARCHITECTURE.md`](.llm/ARCHITECTURE.md) | Sempre (visão geral obrigatória) |
| [`.llm/BUSINESS_RULES.md`](.llm/BUSINESS_RULES.md) | Alterações em lógica, prompts, validações |
| [`.llm/API_CONTRACT.md`](.llm/API_CONTRACT.md) | Alterações em endpoints, DTOs, streaming |
| [`.llm/DATA_MODEL.md`](.llm/DATA_MODEL.md) | Alterações em types, schemas, persistência |
| [`.llm/COMPONENT_MAP.md`](.llm/COMPONENT_MAP.md) | Alterações em UI React |
| [`.llm/DESIGN_SYSTEM.md`](.llm/DESIGN_SYSTEM.md) | Alterações visuais (cores, layout, CSS) |
| [`.llm/DEPENDENCY_GRAPH.md`](.llm/DEPENDENCY_GRAPH.md) | Adição de dependências ou refatoração |
| [`.llm/CONVENTIONS.md`](.llm/CONVENTIONS.md) | Naming, commits, estrutura de diretórios |

## Regras Imperativas

1. **KISS & YAGNI**: Sem abstrações prematuras. Resolva o problema atual.
2. **Diff-Only**: Altere apenas o necessário. Nunca reescreva arquivos inteiros.
3. **Tipagem**: Type hints obrigatórios (Python) e TypeScript strict (Frontend).
4. **Segurança**: Nunca exponha secrets. Respeite guardrails existentes.
5. **Docs sync**: Alterações estruturais → atualizar `.llm/` correspondente no mesmo commit.
