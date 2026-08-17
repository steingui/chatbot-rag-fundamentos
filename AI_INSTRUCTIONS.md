# Diretrizes para IA (Engenharia e Arquitetura)

## 1. Princípios de Arquitetura (Monorepo)
O projeto unifica Backend (FastAPI), Pipelines de Dados (Scraping/Ingestão) e RAG na mesma codebase.
A estrutura deve seguir:
- `/backend`: Lógica da API REST (FastAPI). Deve ser escalável e dividida por domínio (routes, services, core).
- `/backend/rag`: O "Cérebro". Lógica do LangChain, prompts e chain definitions. Isolado do transporte HTTP.
- `/pipelines`: Scripts standalone e jobs (Airflow/Cron). Scrapers de dados políticos e scripts de ingestão (ChromaDB).
- `/frontend`: Interface Web (Next.js ou Vite). Responsável pelo consumo da API.
- `/data`: Armazenamento local temporário. `docs/` para Markdown cru e `chroma_db/` para os vetores.

## 2. Padrões de Código (Python)
- **KISS & YAGNI**: Sem super-abstrações prematuras.
- **Tipagem**: Uso obrigatório de Type Hints (`typing`) e `pydantic` para validação de contratos.
- **Injeção de Dependência**: Usar o padrão de `Depends()` do FastAPI para passar banco de dados e LLMs.
- **Variáveis de Ambiente**: Centralizadas via `pydantic-settings`. Nunca hardcoded.

## 3. Design System (Frontend)
- **Identidade Visual**: Focada em transparência e dados políticos (Sóbrio, fontes sem serifa modernas, data-viz amigável).
- **Tecnologia**: Tailwind CSS + Shadcn/UI (Componentes reutilizáveis sem lock-in).
- **Responsividade**: Mobile-first, focando no consumo rápido de informações pelos eleitores.

## 4. Comportamento da IA
- Escrever código legível antes de código "inteligente".
- Alterar/Sugerir apenas o estritamente necessário (sem reescrever arquivos grandes inteiros).
- Respeitar a separação de responsabilidades descrita no tópico 1.
