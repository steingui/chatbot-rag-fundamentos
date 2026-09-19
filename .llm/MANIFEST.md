# MANIFEST — Índice de Carga Sob Demanda

> Fonte única de roteamento de contexto. Antes de ler qualquer documento em
> `.llm/`, consulte esta tabela e carregue **somente** o que a tarefa exigir.
> Orçamento em tokens estimado como `bytes/4`.

## Roteamento declarativo (tarefa → documentos)

| Tarefa | Documentos | Custo |
|--------|-----------|-------|
| Visão geral da arquitetura | [`ARCHITECTURE.md`](ARCHITECTURE.md) | ~1.5K |
| Endpoints, DTOs, SSE, rate limits | [`API_CONTRACT.md`](API_CONTRACT.md) + [`DATA_MODEL.md`](DATA_MODEL.md) | ~2.0K |
| Lógica RAG, prompts, validações | [`BUSINESS_RULES.md`](BUSINESS_RULES.md) + [`ARCHITECTURE.md`](ARCHITECTURE.md) | ~3.3K |
| UI React, componentes, store | [`COMPONENT_MAP.md`](COMPONENT_MAP.md) + [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) | ~1.8K |
| Schema, tipos, persistência | [`DATA_MODEL.md`](DATA_MODEL.md) | ~1.0K |
| Dependências, refatoração | [`DEPENDENCY_GRAPH.md`](DEPENDENCY_GRAPH.md) | ~1.2K |
| Naming, commits, convenções | [`CONVENTIONS.md`](CONVENTIONS.md) | ~0.9K |

## Regras de carga

1. Tarefa trivial (typo, README, formatação) → **não carregue nenhum `.llm/`**.
2. Custo total da carga é acumulativo: comece pelo documento mais barato que
   responda à dúvida; carregue mais só se necessário.
3. Em caso de dúvida, comece por [`ARCHITECTURE.md`](ARCHITECTURE.md).
4. Qualquer alteração estrutural deve atualizar o `.llm/` correspondente no
   mesmo commit (docs nunca ficam stale).

## Índice de documentos

| Arquivo | Tokens | Conteúdo |
|---------|-------:|----------|
| `ARCHITECTURE.md` | ~1.5K | Visão geral, camadas, fluxo de dados, deploy |
| `BUSINESS_RULES.md` | ~1.8K | Regras de negócio, domínio, invariantes |
| `API_CONTRACT.md` | ~1.0K | Contratos HTTP (endpoints, DTOs, SSE, rate limits) |
| `DATA_MODEL.md` | ~1.0K | Modelos de dados (frontend types, Pydantic, SQLite) |
| `COMPONENT_MAP.md` | ~1.1K | Componentes React + store Zustand |
| `DESIGN_SYSTEM.md` | ~0.7K | Tokens de design, paleta, tipografia |
| `DEPENDENCY_GRAPH.md` | ~1.2K | Grafo de dependências (Python + Node) |
| `CONVENTIONS.md` | ~0.9K | Convenções de código, naming, commit, branch, testes |
