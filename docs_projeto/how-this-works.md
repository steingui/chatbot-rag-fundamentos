# Como este Projeto Funciona (RAG na Prática)

O projeto implementa uma arquitetura **RAG (Retrieval-Augmented Generation)** conectada a uma API REST (FastAPI no GCP Cloud Run) e um frontend em React + Vite (Firebase Hosting), com monitoramento, auto-cura autônoma e pipeline de QA multi-agente via CI/CD.

O fluxo é dividido em quatro componentes principais: **Scraping**, **Ingestão Híbrida**, **Auto-Cura & QA Autônomo (CI/CD)** e **Consulta (API & Web)**.

---

## 1. Etapa de Scraping (`pipelines/scrapers/`)
Objetivo: Coletar e estruturar dados políticos e públicos em arquivos Markdown (`data/docs/`).
- **scraper_camara.py**: Histórico de votações e ementas legislativas da Câmara dos Deputados.
- **scraper_senado.py**: Proposições, votações, discursos e despesas da cota parlamentar (CEAPS) do Senado Federal.
- **scraper_tse_bens.py**: Patrimônio de candidatos e doações de campanha (DivulgaCandContas).
- **querido_diario_scraper.py**: Nomeações, atos e licitações municipais da Open Knowledge Brasil.
- **rss_fact_checking_scraper.py**: Checagens de fatos (G1 Fato ou Fake, Aos Fatos, Estadão Verifica, Agência Pública).
- **scraper_transparencia.py**: Emendas parlamentares PIX e execução orçamentária (CGU / Portal da Transparência).

---

## 2. Etapa de Ingestão Híbrida (`pipelines/ingestion/pinecone_ingestor.py`)
Objetivo: Processar documentos e sincronizar vetores no Pinecone com busca híbrida.
1. **Leitura**: Carrega arquivos `.md` da pasta `data/docs/`.
2. **Chunking**: Fatia textos com `RecursiveCharacterTextSplitter` (1000 caracteres / 200 overlap).
3. **Vetorização Híbrida**: Gera embeddings densos (HuggingFace Inference API) e vetores esparsos (BM25 com `pinecone-text`) para busca híbrida com Reciprocal Rank Fusion (RRF).
4. **Pinecone**: Persiste e atualiza os embeddings no índice serverless `rag-fundamentos`.

---

## 3. Monitoramento, QA Multi-Agente e Auto-Cura (CI/CD)
Objetivo: Garantir resiliência, sanitizar dados, validar regras de negócio e auto-corrigir falhas de CI/CD.
- **Diagnóstico Autônomo (Google Gemini)**: Analisa stack traces e aplica patches automáticos (`[LLM-COMMIT-AND-HEAL]`).
- **Pipeline de QA Multi-Agente (`autonomous_qa_pipeline.yml`)**:
  - **Pytest**: Suíte unitária e de regras de negócio.
  - **Agente Testador RAG-AI**: Testes de segurança, injeção de prompt e suporte a personas (eleitor, jornalista, pesquisador, QA adversarial).
  - **Triagem, Worker Pool & Code Reviewer**: Agentes que classificam falhas, aplicam correções e efetuam revisão autônoma de código.

---

## 4. Etapa de Consulta (`backend/api/` e `frontend/src/`)
Objetivo: Atender requisições em tempo real com segurança, baixa latência e fontes auditáveis.
1. **Segurança & Middleware**: Rate limiting via `slowapi`, sanitização anti-prompt-injection (`guardrails.py`), validação de Origin (`SEC-005`) e Security Headers (`SEC-003`).
2. **Endpoint SSE**: Frontend React se comunica via Server-Sent Events (`/chat/stream`) para respostas em streaming incremental.
3. **Recuperação Híbrida & Cache**: Busca vetorial híbrida no Pinecone + busca complementar via DuckDuckGo News. Respostas recorrentes são servidas pelo `global_rag_cache` (TTL 5min).
4. **Síntese LLM (OpenRouter Multi-Provider)**: Suporte dinâmico a modelos (Gemini 3.7/3.6 Flash, Llama 3.3 70B, DeepSeek R1), retornando a síntese formatada com badges de fontes categorizadas.
5. **Analytics**: SQLite rastreia e canoniza as perguntas mais frequentes para sugestões populares (`/suggestions`).

---

## Fluxo Geral da Arquitetura

```mermaid
graph TD
    subgraph Ingestao["1. Coleta e Ingestão (GitHub Actions)"]
        Scrapers["Scrapers Python<br>(Câmara, Senado, TSE, OKBR, CGU, RSS)"] --> Docs["Arquivos Markdown<br>(data/docs/*.md)"]
        Docs --> Ingestor["Pinecone Ingestor<br>(Dense + BM25 Sparse Embeddings)"]
        Ingestor --> Pinecone[("Pinecone Vector DB<br>Serverless")]
    end

    subgraph AutoCura["2. Auto-Cura & QA Multi-Agente"]
        QA["Autonomous QA Pipeline<br>(Pytest + RAG-AI Tester)"] --> Triage["Agentes Triage, Pool & Reviewer"]
        Triage --> Gemini["Google Gemini<br>(Análise de Erros & Codebase)"]
        Gemini -->|Auto-Commit| GitBot["[LLM-COMMIT-AND-HEAL] / PRs"]
    end

    subgraph Producao["3. Aplicação em Produção (GCP & Firebase)"]
        User(("Usuário")) -->|Prompt / Chat| Front["Frontend React + Vite<br>(Firebase Hosting)"]
        Front -->|API REST / SSE| Back["FastAPI Backend<br>(GCP Cloud Run)"]
        Back -->|1. Hybrid Search (Dense+BM25)| Pinecone
        Back -->|2. Prompt Augmentation| OpenRouter["OpenRouter LLM<br>(Gemini 3.7, Llama 3.3, DeepSeek)"]
        OpenRouter -->|3. Resposta + Citação| Back
        Back -->|4. Stream SSE| Front
    end
```

