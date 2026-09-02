[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]
# Relatório Autônomo de Monitoramento e Auto-Cura

**Status Pinecone:** `OK` | **Total Vetores:** 2314

## Auditoria e Auto-Cura de Documentos Local (`data/docs`)
- **Total de Arquivos:** 0
- **Arquivos Auto-Corrigidos:** 0
- **Arquivos Purgados (Inválidos/Vazios):** 0

## Últimas 5 Execuções por Pipeline de Ingestão (GitHub Actions)
### Monitoramento Autônomo e Auto-Cura de Ingestões
  - Execução ID `33565090508` (2026-09-01T22:12:12Z): `in_progress`
  - Execução ID `33546943213` (2026-09-01T19:00:12Z): `success`
  - Execução ID `33519320945` (2026-09-01T14:24:45Z): `success`
  - Execução ID `33507308836` (2026-09-01T12:22:21Z): `success`
  - Execução ID `33494236422` (2026-09-01T09:49:38Z): `success`

### Ingestão Diária - Câmara dos Deputados
  - Execução ID `33564958045` (2026-09-01T22:10:39Z): `success`
  - Execução ID `33546806358` (2026-09-01T18:58:46Z): `success`
  - Execução ID `33519203967` (2026-09-01T14:23:35Z): `success`
  - Execução ID `33489869974` (2026-09-01T08:59:29Z): `success`
  - Execução ID `33463062924` (2026-09-01T02:34:46Z): `success`

### Ingestão Diária - Fact Checking (RSS Multi-Agências)
  - Execução ID `33493987038` (2026-09-01T09:46:41Z): `success`
  - Execução ID `33386712098` (2026-08-31T11:23:11Z): `success`
  - Execução ID `33306095638` (2026-08-30T10:17:00Z): `success`
  - Execução ID `33264374330` (2026-08-29T16:58:06Z): `success`
  - Execução ID `33250226314` (2026-08-29T11:29:01Z): `failure`

### Ingestão Semanal - Portal da Transparência / CGU
  - Execução ID `33486003757` (2026-09-01T08:14:16Z): `success`

### Ingestão Diária - Querido Diário (Atos Municipais)
  - Execução ID `33485008609` (2026-09-01T08:02:11Z): `success`
  - Execução ID `33375414567` (2026-08-31T08:58:42Z): `success`
  - Execução ID `33301982621` (2026-08-30T08:36:03Z): `success`
  - Execução ID `33264375773` (2026-08-29T16:58:08Z): `success`
  - Execução ID `33245563849` (2026-08-29T09:28:10Z): `failure`

### Ingestão Diária - Senado Federal
  - Execução ID `33476455509` (2026-09-01T06:10:11Z): `success`
  - Execução ID `33365942319` (2026-08-31T06:52:23Z): `success`
  - Execução ID `33296839457` (2026-08-30T06:25:01Z): `success`
  - Execução ID `33241617652` (2026-08-29T07:46:35Z): `success`
  - Execução ID `33171880418` (2026-08-28T12:38:00Z): `success`

### Ingestão Mensal - PDFs e Planos de Governo (TSE)
  - Execução ID `33466222601` (2026-09-01T03:26:32Z): `success`

### Geração de Prompts Dinâmicos (Cronjob LLM)
  - Execução ID `33409317376` (2026-08-31T15:35:31Z): `success`

### Ingestão Semanal - TSE (Bens e Financiamentos)
  - Execução ID `33376552631` (2026-08-31T09:12:53Z): `success`

### Ingestão Semanal - TSE DivulgaCandContas (Prestação de Contas)
  - Execução ID `33299461754` (2026-08-30T07:32:42Z): `success`

## Diagnóstico Autônomo de LLM (`[LLM-COMMIT-AND-HEAL]`)
**[Diagnóstico Gemini 3.6 Flash (Auto-Curado via Tool Calling)]**
- **Tool Invocada:** `apply_file_patch` em `pipelines/ingestion/pinecone_ingestor.py` -> Resultado: Sucesso: Arquivo pipelines/ingestion/pinecone_ingestor.py curado fisicamente.
