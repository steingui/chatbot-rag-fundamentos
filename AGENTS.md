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

**Nunca copie versões ou valores para documentação.** Referencie os arquivos acima.

---

## 2  Estrutura do Projeto

```
.
├── backend/api/      # FastAPI — main.py, guardrails.py, analytics.py, auth.py, firestore_db.py
├── backend/rag/      # LangChain + Pinecone — chat.py, cache.py, sparse_encoder.py, semantic_router.py, jev_client.py
├── backend/workers/  # Workers de ingestão assíncrona
├── frontend/         # React + Vite + TypeScript + Zustand
├── pipelines/        # ingestion/ e scrapers/ de dados legislativos
├── tests/            # pytest — segurança, performance, features
├── data/             # Dados brutos e processados
├── .llm/             # Documentação sob demanda — consulte .llm/MANIFEST.md
├── .github/workflows/ # GitHub Actions — ingestão diária/semanal + monitoramento
└── docs_projeto/     # Documentação acadêmica + resultados de teste
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

```bash
# Backend
pip install -r requirements.txt
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 10000
pytest tests/ -q

# Frontend
cd frontend && npm install
npm run dev          # dev server
npm run build        # tsc -b && vite build
npm run lint         # eslint .
npm run test         # vitest run

# Docker
docker build -t chatbot-rag .
docker run -p 10000:10000 --env-file .env chatbot-rag

# Contexto & logs
codegraph sync .
./scripts/fetch_logs.sh 30
```

---

## 5  Fluxo de Trabalho do Agente

1. **Leia este arquivo** para entender o contrato.
2. **Inspecione os arquivos de build** (seção 1) para versões e dependências atuais.
3. **Carregue documentação sob demanda** via [`.llm/MANIFEST.md`](.llm/MANIFEST.md) — leia
   somente o documento relevante à tarefa. Tarefa trivial (typo, README) → nenhum `.llm/`.
4. **Rode testes antes e depois** de alterações para validar regressão.
5. **Suíte verde → commit + push automático**: quando os testes escritos seguindo
   SDD (vermelho → verde) passarem e a suíte completa do projeto estiver verde,
   **pode** executar a skill `cp` (análise do diff, commits agrupados por contexto
   lógico em Conventional Commits e `git push` final) sem pedir confirmação.
   Nunca commitar com suíte vermelha, testes ignorados ou `lint` com erros.

### Princípios de edição

- **KISS & YAGNI**: Sem abstrações especulativas. Resolva o problema atual.
- **Diff-Only**: Altere apenas o necessário. Nunca reescreva arquivos inteiros.
- **Tipagem**: Type hints obrigatórios (Python). TypeScript strict (Frontend).
- **Docs sync**: Alterações estruturais → atualize o `.llm/` correspondente no mesmo commit.
- **Backlog sync**: Toda implementação concluída **deve** atualizar o backlog em
  `backlog/` no mesmo commit, marcando o item correspondente com o sufixo
  `[DONE]` e referenciando o artefato entregue (arquivo/PR). Nunca deixe um item
  de backlog implementado sem o marcador.

---

## 6  Segurança

1. **Secrets/PII**: Nunca logar, expor ou hardcodar. Toda secret vem de env vars (`.env.example`).
2. **Validação de entrada**: Toda entrada do usuário passa por `backend/api/guardrails.py`.
3. **Autorização**: Respeitar rate limiting (`slowapi`) e guardrails existentes.
4. **Endpoints**: Não expor rotas administrativas ou de debug sem autenticação.
5. **Serialização**: Usar schemas tipados; nunca deserializar dados arbitrários.
6. **HTTP externo**: Toda chamada externa usa timeout e retry.
7. **Persistência**: Dados sensíveis nunca em plain text. Pinecone metadata sem PII.
8. **Dependências**: Não adicionar sem justificativa. Preferir as já existentes.

---

## 7  Convenções Git

- **Commits**: Mensagem descritiva em português, imperativo. Exemplo: `Corrige fallback de LLM no chat`.
- **Branches**: `feat/`, `fix/`, `docs/`, `refactor/` + slug curto.
- **PRs**: Título descritivo + descrição do que muda e por quê.
- **Verificação pré-commit**: `git diff --check`.

---

## 8  Carregamento Seletivo de Diretrizes

- Consulte [`.llm/MANIFEST.md`](.llm/MANIFEST.md) para roteamento e orçamento de tokens.
- Carregue **somente** o documento relevante à tarefa.
- Em caso de dúvida, comece por `.llm/ARCHITECTURE.md`.
