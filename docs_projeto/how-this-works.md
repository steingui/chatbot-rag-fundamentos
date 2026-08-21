# Como este Projeto Funciona (RAG na Prática)

O projeto implementa uma arquitetura **RAG (Retrieval-Augmented Generation)**, conectada a uma API REST (FastAPI) pronta para deploy no Hugging Face Spaces / Render.

O fluxo é dividido em três etapas principais: **Scraping**, **Ingestão** e **Consulta (API)**.

## 1. Etapa de Scraping (`pipelines/scrapers/`)
Objetivo: Coletar dados da vida real (Câmara, TSE, Portais de Notícias).
- **scraper_camara.py**: Histórico de votações e Ementas.
- **scraper_tse_bens.py**: Dados patrimoniais e financiadores de campanha.
- **scraper_tse_pdfs.py**: Planos de governo passados por OCR/LLM (refinamento).
- **scraper_rss.py**: Fact-Checking direto do G1 Fato ou Fake.
Os scrapers salvam o resultado em Markdown (`.md`) na pasta `data/docs/`.

## 2. Etapa de Ingestão (`pipelines/ingestion/pinecone_ingestor.py`)
Objetivo: Preparar os documentos e armazená-los no Vector DB (Nuvem).

1. **Carregamento**: Lê os arquivos `.md` da pasta `data/docs/`.
2. **Fatiamento (Chunking)**: Quebra os documentos em pedaços menores (1000 caracteres) para respeitar o limite de contexto do LLM.
3. **Vetorização**: Converte chunks em vetores usando o modelo open-source da HuggingFace (`all-MiniLM-L6-v2`).
4. **Armazenamento**: Grava os vetores no **Pinecone** (Vector DB em nuvem).

## 3. Etapa de Consulta (`backend/api/main.py` e `backend/rag/chat.py`)
Objetivo: Expor a IA em uma API REST com memória de sessão e citação de fontes.

1. **Endpoint**: O usuário envia um POST para a API com sua pergunta e `session_id`.
2. **Recuperação (Pinecone)**: O Pinecone retorna os **15** chunks mais similares.
3. **Prompt Augmentation**: O contexto, histórico e a pergunta são injetados no prompt.
4. **Geração (LLM)**: O modelo **Google Gemma 4 (31B)** via OpenRouter gera a resposta precisa, e a API devolve o texto mais as fontes citadas.

---
**Resumo do Fluxo:**

```mermaid
graph TD
    %% Estilos Simplificados
    classDef github fill:#171515,color:#fff,stroke:#fff
    classDef pinecone fill:#f0f0f0,color:#000,stroke:#333
    classDef render fill:#000,color:#fff,stroke:#333
    classDef openrouter fill:#6236ff,color:#fff,stroke:#333
    classDef hf fill:#ffcc00,color:#000,stroke:#333

    subgraph "1. Pipelines de Ingestão (GitHub Actions)"
        A[Cron Jobs<br>Diário/Semanal/Mensal]:::github -->|Executa| B(Scrapers Python:<br>Câmara, TSE, RSS)
        B -->|Extrai Textos (.md)| C[Hugging Face API<br>all-MiniLM-L6-v2]:::hf
        C -->|Gera Embeddings| D[(Pinecone Vector DB)]:::pinecone
    end

    subgraph "2. Produção (Render)"
        U((Usuário)) -->|POST /chat| F[FastAPI Backend]:::render
        F -.->|1. Busca Contexto (k=15)| D
        D -.->|2. Retorna Vetores Relevantes| F
        F -.->|3. Envia Prompt + Contexto| G[OpenRouter API<br>Gemma 4 31B]:::openrouter
        G -.->|4. Resposta Final| F
        F -->|5. Retorna Resposta + Fontes| U
    end
```
