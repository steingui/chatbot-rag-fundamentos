# AGENTS.md — Contrato de Governança para Agentes de Código

> Documento provider-agnostic. Qualquer LLM/agente que opere neste repositório
> **DEVE** seguir estas diretrizes antes de ler ou alterar qualquer arquivo.

---

## 1  Fonte de Verdade

| Aspecto | Arquivo(s) canônicos |
|---------|---------------------|
| Python runtime | `.python-version` |
| Dependências backend | `requirements.txt`, `requirements-api.txt` |
| Dependências frontend | `frontend/package.json` |
| Build & deploy | `Dockerfile`, `cloudbuild.yaml`, `firebase.json` |
| CI/CD | `cloudbuild.yaml`, `.github/workflows/*.yml` |
| Env vars esperadas | `.env.example` |
| Lint frontend | `frontend/eslint.config.js` |
| TypeScript config | `frontend/tsconfig*.json` |
| Testes backend | `tests/test_*.py` (pytest) |
| Testes frontend | `frontend/` (vitest) |
| Arquitetura detalhada | `.llm/ARCHITECTURE.md` |
| Regras de negócio | `.llm/BUSINESS_RULES.md` |
| Contrato de API | `.llm/API_CONTRACT.md` |
| Modelo de dados | `.llm/DATA_MODEL.md` |
| Mapa de componentes | `.llm/COMPONENT_MAP.md` |
| Design system | `.llm/DESIGN_SYSTEM.md` |
| Grafo de dependências | `.llm/DEPENDENCY_GRAPH.md` |
| Convenções | `.llm/CONVENTIONS.md` |

**Nunca copie versões ou valores para documentação.** Referencie os arquivos acima
como fonte de verdade.

---

## 2  Estrutura do Projeto

```
.
├── backend/
│   ├── api/          # FastAPI — main.py, guardrails.py, analytics.py
│   ├── rag/          # LangChain + Pinecone — chat.py, retriever.py, llm_fallback.py, cache.py
│   └── workers/      # Workers de ingestão assíncrona
├── frontend/         # React + Vite + TypeScript + Zustand
├── pipelines/
│   ├── ingestion/    # Scripts de ingestão de dados
│   └── scrapers/     # Scrapers de dados legislativos
├── tests/            # pytest — segurança, performance, features
├── data/             # Dados brutos e processados
├── .llm/             # Documentação de engenharia reversa (carregar sob demanda)
├── .github/workflows/ # GitHub Actions — ingestão diária/semanal + monitoramento
└── docs_projeto/     # Documentação do projeto acadêmico
```

---

## 3  Stack Tecnológica

| Camada | Tecnologias |
|--------|------------|
| Backend | Python 3.11 · FastAPI · Uvicorn · LangChain · Pinecone |
| Frontend | React 18 · TypeScript · Vite · Zustand · Vitest |
| Infra | Docker · GCP Cloud Run (API) · Firebase Hosting (Static) · Cloud Build |
| LLMs | OpenRouter (multi-provider) · Google AI (Gemini) |
| Vector DB | Pinecone (hybrid search: dense + BM25 sparse) |

---

## 4  Comandos Executáveis

### Backend
```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar API local
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 10000

# Testes
pytest tests/ -q

# Type checking (se disponível)
# Não há mypy configurado — use type hints mesmo assim
```

### Frontend
```bash
cd frontend

# Instalar
npm install

# Dev server
npm run dev

# Build
npm run build        # tsc -b && vite build

# Lint
npm run lint         # eslint .

# Testes
npm run test         # vitest run
```

### Docker
```bash
docker build -t chatbot-rag .
docker run -p 10000:10000 --env-file .env chatbot-rag
```

### Otimização de Contexto para Agentes
```bash
# Atualizar / verificar o índice do CodeGraph
codegraph sync .

# Empacotar repositório em arquivo único para LLMs via web
repomix
```


---

## 5  Fluxo de Trabalho do Agente

### Antes de qualquer edição:

1. **Leia este arquivo** para entender o contrato.
2. **Inspecione os arquivos de build** (seção 1) para entender versões e dependências atuais.
3. **Carregue `.llm/` sob demanda** — leia apenas o documento relevante à tarefa:
   - Alteração em endpoint → `.llm/API_CONTRACT.md`
   - Alteração em UI → `.llm/COMPONENT_MAP.md` + `.llm/DESIGN_SYSTEM.md`
   - Alteração em lógica RAG → `.llm/BUSINESS_RULES.md` + `.llm/ARCHITECTURE.md`
   - Alteração em schema/tipos → `.llm/DATA_MODEL.md`
   - Refatoração/deps → `.llm/DEPENDENCY_GRAPH.md`
   - Naming/estrutura → `.llm/CONVENTIONS.md`
4. **Rode testes antes e depois** de alterações para validar regressão.

### Princípios de edição:

- **KISS & YAGNI**: Resolva o problema atual, sem abstrações especulativas.
- **Diff-Only**: Altere apenas o necessário. Nunca reescreva arquivos inteiros.
- **Tipagem**: Type hints obrigatórios (Python). TypeScript strict (Frontend).
- **Docs sync**: Alterações estruturais → atualize o `.llm/` correspondente no mesmo commit.

---

## 6  Segurança

> Regras invioláveis — qualquer agente **DEVE** seguir sem exceção.

1. **Secrets/PII**: Nunca logar, expor ou hardcodar. Toda secret vem de variáveis de ambiente (ver `.env.example`).
2. **Validação de entrada**: Toda entrada do usuário passa por `backend/api/guardrails.py`. Nunca processar input sem sanitização.
3. **Autorização**: Respeitar rate limiting (`slowapi`) e guardrails existentes.
4. **Endpoints**: Não expor rotas administrativas ou de debug sem autenticação.
5. **Serialização**: Usar schemas tipados; nunca deserializar dados arbitrários.
6. **HTTP externo**: Toda chamada externa usa timeout e retry. Nunca confiar em respostas sem validação.
7. **Persistência**: Dados sensíveis nunca em plain text. Pinecone metadata não deve conter PII.
8. **Dependências**: Não adicionar dependências sem justificativa. Preferir as já existentes.

---

## 7  Convenções Git

- **Commits**: Mensagem descritiva em português, imperativo. Exemplo: `Corrige fallback de LLM no chat`.
- **Branches**: `feat/`, `fix/`, `docs/`, `refactor/` + slug curto.
- **PRs**: Título descritivo + descrição do que muda e por quê.
- **Verificação pré-commit**: `git diff --check` para evitar whitespace errors.

---

## 8  Carregamento Seletivo de Diretrizes

Os documentos em `.llm/` são **pesados**. Para economia de contexto:

- Carregue **somente** o(s) documento(s) relevante(s) à tarefa atual.
- Se a tarefa não exige conhecimento arquitetural detalhado, **não carregue nenhum `.llm/`**.
- Use a tabela da seção 5 como guia de quando carregar cada documento.
- Em caso de dúvida, comece por `.llm/ARCHITECTURE.md` (visão geral) e carregue mais apenas se necessário.
