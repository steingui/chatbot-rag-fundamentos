# Execução das Pipelines de Ingestão (RAG)

Após a refatoração, a camada de extração (Scrapers) foi separada da camada de persistência (Ingestão), garantindo que falhas em uma fonte de dados não quebrem a ingestão das demais.

## 1. Scrapers (Extração de Dados)

Cada script abaixo é responsável por coletar informações de uma fonte distinta. Eles salvam os resultados em arquivos `.md` na pasta `data/docs`.

**Câmara dos Deputados (Votações Diárias)**
Extrai as últimas votações e ementas.
```bash
venv/bin/python pipelines/scrapers/scraper_camara.py
```

**TSE (Bens e Financiamentos)**
Extrai dados patrimoniais e doadores de campanha dos candidatos.
```bash
venv/bin/python pipelines/scrapers/scraper_tse_bens.py
```

**TSE (Planos de Governo / PDFs)**
Simula a extração de propostas de governo refinadas (OCR/LLM).
```bash
venv/bin/python pipelines/scrapers/scraper_tse_pdfs.py
```

**Fact-Checking via RSS (G1 Fato ou Fake)**
Coleta o feed de checagem de fatos para desmentir fake news.
```bash
venv/bin/python pipelines/scrapers/scraper_rss.py
```

---

## 2. Ingestão Centralizada (Pinecone)

O arquivo `pinecone_ingestor.py` serve como **módulo central**. Ele lê TODOS os arquivos Markdown dentro de `data/docs/`, gera os *embeddings* (HuggingFace) e salva os chunks no Pinecone.

```bash
venv/bin/python pipelines/ingestion/pinecone_ingestor.py
```

---

## 3. Acionamento Automático (CI/CD)

As execuções de Produção estão configuradas no **GitHub Actions** na pasta `.github/workflows/`. Foram separadas em três pipelines por frequência de atualização:

- `ingest_diario_camara.yml` (Diário às 00h e 12h)
- `ingest_semanal_tse.yml` (Semanal - Segundas às 02h)
- `ingest_mensal_pdfs.yml` (Mensal - Dia 1º de cada mês)

**Para disparar as actions manualmente pelo terminal:**
```bash
gh workflow run ingest_diario_camara.yml
```

**Para acompanhar os logs da execução em tempo real:**
```bash
gh run watch
```
