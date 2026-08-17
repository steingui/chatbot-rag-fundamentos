# Como este Projeto Funciona (RAG na Prática)

O projeto implementa uma arquitetura **RAG (Retrieval-Augmented Generation)**, conectada a uma API REST (FastAPI) pronta para deploy no Hugging Face Spaces.

O fluxo é dividido em três etapas principais: **Scraping**, **Ingestão** e **Consulta (API)**.

## 1. Etapa de Scraping (`pipelines/scrapers/scraper.py`)
Objetivo: Coletar dados da vida real (ex: Histórico de Votações da Câmara).
- Conecta em APIs abertas, extrai dados cruciais, processa as informações e salva o resultado no formato Markdown (`.md`) na pasta `data/docs/`.

## 2. Etapa de Ingestão (`pipelines/ingestion/ingest.py`)
Objetivo: Preparar os documentos e armazená-los no Vector DB (Nuvem).

1. **Carregamento**: Lê os arquivos `.md` da pasta `data/docs/`.
2. **Fatiamento (Chunking)**: O `RecursiveCharacterTextSplitter` quebra os documentos em pedaços menores (1000 caracteres) para respeitar o limite de contexto do LLM.
3. **Vetorização**: Converte chunks em vetores usando o modelo open-source da HuggingFace (`all-MiniLM-L6-v2`).
4. **Armazenamento**: Grava os vetores no **Pinecone** (Vector DB em nuvem). Isso nos permite rodar o backend em servidores gratuitos que resetam o disco local a cada deploy.

## 3. Etapa de Consulta (`backend/api/main.py` e `backend/rag/chat.py`)
Objetivo: Expor a IA em uma API REST.

1. **Endpoint**: O usuário envia um POST para a API com sua pergunta.
2. **Recuperação (Pinecone)**: A pergunta é vetorizada e o Pinecone retorna os top 3 chunks mais similares.
3. **Prompt Augmentation**: O contexto e a pergunta são injetados no prompt.
4. **Geração (LLM)**: O modelo (via OpenRouter) lê o contexto e gera uma resposta precisa.

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

    subgraph "1. Pipeline de Ingestão (GitHub Actions)"
        A[Cron Job Diario]:::github -->|Baixa dados da Câmara| B(Scraper Python)
        B -->|Extrai Textos| C[Hugging Face API<br>all-MiniLM-L6-v2]:::hf
        C -->|Gera Embeddings| D[(Pinecone Vector DB)]:::pinecone
    end

    subgraph "2. Produção (Render)"
        U((Usuário)) -->|POST /chat| F[FastAPI Backend]:::render
        F -.->|1. Busca Contexto| D
        D -.->|2. Retorna Vetores Relevantes| F
        F -.->|3. Envia Prompt + Contexto| G[OpenRouter API<br>Llama-3 8B]:::openrouter
        G -.->|4. Resposta Final| F
        F -->|5. Retorna Mensagem| U
    end
```
