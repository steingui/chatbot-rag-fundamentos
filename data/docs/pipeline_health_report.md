[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]
# Relatório Autônomo de Monitoramento e Auto-Cura

**Status Pinecone:** `OK` | **Total Vetores:** 1153

## Auditoria e Auto-Cura de Documentos Local (`data/docs`)
- **Total de Arquivos:** 0
- **Arquivos Auto-Corrigidos:** 0
- **Arquivos Purgados (Inválidos/Vazios):** 0

## Últimas 5 Execuções por Pipeline de Ingestão (GitHub Actions)
### Monitoramento Autônomo e Auto-Cura de Ingestões
  - Execução ID `32586304445` (2026-08-22T16:58:06Z): `in_progress`
  - Execução ID `32585674287` (2026-08-22T16:45:32Z): `success`
  - Execução ID `32585253159` (2026-08-22T16:37:13Z): `success`
  - Execução ID `32584752333` (2026-08-22T16:27:25Z): `success`
  - Execução ID `32584401819` (2026-08-22T16:20:25Z): `success`

### .github/workflows/monitor_and_heal_pipelines.yml
  - Execução ID `32586218209` (2026-08-22T16:56:20Z): `failure`

### Ingestão Diária - Câmara dos Deputados
  - Execução ID `32583973239` (2026-08-22T16:11:42Z): `success`
  - Execução ID `32577980083` (2026-08-22T14:11:42Z): `success`
  - Execução ID `32572616606` (2026-08-22T12:18:05Z): `success`
  - Execução ID `32567018717` (2026-08-22T10:12:47Z): `success`
  - Execução ID `32561876831` (2026-08-22T08:17:06Z): `success`

### Ingestão Semanal - TSE (Bens e Financiamentos)
  - Execução ID `32549426068` (2026-08-22T03:36:09Z): `success`

### Ingestão Diária - Senado Federal
  - Execução ID `32545830880` (2026-08-22T02:17:06Z): `success`

### Pipeline de Ingestão de Dados (Scraping + RAG)
  - Execução ID `32502981966` (2026-08-21T16:27:06Z): `success`
  - Execução ID `32497539540` (2026-08-21T15:25:46Z): `success`
  - Execução ID `32444416473` (2026-08-21T03:43:53Z): `success`
  - Execução ID `32386122911` (2026-08-20T15:26:15Z): `success`
  - Execução ID `32329032672` (2026-08-20T03:39:45Z): `success`

## Diagnóstico Autônomo de LLM (`[LLM-COMMIT-AND-HEAL]`)
**[Diagnóstico Gemini 3.6 Flash (Google Antigravity com Contexto de Codebase)]**
### Causa Raiz
A etapa `Install Dependencies` no workflow `monitor_and_heal_pipelines.yml` instala dependências individualmente via `pip install` em vez de utilizar o `requirements.txt`. Com isso, a biblioteca **`pypdf`** (dependência obrigatória do `PyPDFDirectoryLoader` em `pinecone_ingestor.py`) e a nova SDK `pinecone` (em substituição ao pacote legado `pinecone-client`) ficam ausentes no ambiente do job, resultando em `ModuleNotFoundError` durante a execução da re-ingestão (`Re-Ingest Fixed Documents to Pinecone`).

---

### Correção

#### Diff no Workflow (`.github/workflows/monitor_and_heal_pipelines.yml`):

```diff
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
-         pip install requests pinecone-client sentence-transformers langchain-community langchain-pinecone langchain-huggingface langchain-google-genai google-generativeai python-dotenv
+         pip install --prefer-binary -r requirements.txt
+         pip install pypdf pinecone langchain-google-genai google-generativeai
```
