[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]
# Relatório Autônomo de Monitoramento e Auto-Cura

**Status Pinecone:** `OK` | **Total Vetores:** 1131

## Auditoria e Auto-Cura de Documentos Local (`data/docs`)
- **Total de Arquivos:** 161
- **Arquivos Auto-Corrigidos:** 0
- **Arquivos Purgados (Inválidos/Vazios):** 0

## Últimas 5 Execuções por Pipeline de Ingestão (GitHub Actions)
### Monitoramento Autônomo e Auto-Cura de Ingestões
  - Execução ID `32581285453` (2026-08-22T15:18:11Z): `success`
  - Execução ID `32581104449` (2026-08-22T15:14:38Z): `failure`

### Ingestão Diária - Câmara dos Deputados
  - Execução ID `32577980083` (2026-08-22T14:11:42Z): `success`
  - Execução ID `32572616606` (2026-08-22T12:18:05Z): `success`
  - Execução ID `32567018717` (2026-08-22T10:12:47Z): `success`
  - Execução ID `32561876831` (2026-08-22T08:17:06Z): `success`
  - Execução ID `32556750071` (2026-08-22T06:21:17Z): `success`

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
Falha ao consultar LLM para diagnóstico: Error code: 401 - {'error': {'message': 'Missing Authentication header', 'code': 401}}
