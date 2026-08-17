# Execução das Pipelines de Ingestão (RAG)

Após a refatoração, a camada de extração (Scrapers) foi separada da camada de persistência (Ingestão), garantindo que falhas em uma fonte de dados não quebrem a ingestão das demais.

## 1. Scrapers (Extração de Dados)

Cada script abaixo é responsável por coletar informações de uma fonte distinta.

**Câmara dos Deputados (Produção)**
Extrai as últimas votações e gera arquivos `.md` na pasta `data/docs`.
```bash
venv/bin/python pipelines/scrapers/scraper_camara.py
```

**Planos de Governo TSE (Esqueleto)**
Criado para a Fase 2. Focado na extração e refinamento de textos usando LLM.
```bash
venv/bin/python pipelines/scrapers/scraper_tse_pdfs.py
```

**Fact-Checking via RSS (Esqueleto)**
Criado para a Fase 2. Focado na coleta de agências de checagem (Lupa, Aos Fatos).
```bash
venv/bin/python pipelines/scrapers/scraper_rss.py
```

---

## 2. Ingestão Centralizada (Pinecone)

O arquivo `pinecone_ingestor.py` serve como **módulo central**. Ele gera os *embeddings* (HuggingFace) e salva os chunks no Pinecone.

Se executado diretamente, ele buscará arquivos `.md` e `.pdf` no diretório local `data/docs` e fará a carga:
```bash
venv/bin/python pipelines/ingestion/pinecone_ingestor.py
```
*(Nota: Os novos scrapers já importam e executam a função `ingest_documents()` em memória, sem necessidade de gravar arquivos intermediários).*

---

## 3. Acionamento Automático (CI/CD)

As execuções de Produção estão configuradas no **GitHub Actions** (`.github/workflows/daily_ingest.yml`). O fluxo ocorre automaticamente às 00h00 e 12h00 (BRT).

**Para disparar a action manualmente pelo terminal:**
```bash
gh workflow run daily_ingest.yml
```

**Para acompanhar os logs da execução em tempo real:**
```bash
gh run watch
```
