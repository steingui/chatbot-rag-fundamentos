[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]
# Relatório Autônomo de Monitoramento e Auto-Cura

**Status Pinecone:** `WARNING` | **Total Vetores:** 0

## Auditoria e Auto-Cura de Documentos Local (`data/docs`)
- **Total de Arquivos:** 0
- **Arquivos Auto-Corrigidos:** 0
- **Arquivos Purgados (Inválidos/Vazios):** 0

## Últimas 5 Execuções por Pipeline de Ingestão (GitHub Actions)
### Monitoramento Autônomo e Auto-Cura de Ingestões
  - Execução ID `32727286169` (2026-08-24T12:28:31Z): `in_progress`
  - Execução ID `32717008209` (2026-08-24T10:29:04Z): `success`
  - Execução ID `32707261700` (2026-08-24T08:37:34Z): `success`
  - Execução ID `32703901657` (2026-08-24T07:57:26Z): `success`
  - Execução ID `32698186140` (2026-08-24T06:38:56Z): `success`

### Ingestão Diária - Câmara dos Deputados
  - Execução ID `32727065879` (2026-08-24T12:25:59Z): `success`
  - Execução ID `32716870877` (2026-08-24T10:27:26Z): `failure`
  - Execução ID `32707126056` (2026-08-24T08:35:56Z): `failure`
  - Execução ID `32698007176` (2026-08-24T06:36:14Z): `success`
  - Execução ID `32690565128` (2026-08-24T04:35:12Z): `success`

### Geração de Prompts Dinâmicos (Cronjob LLM)
  - Execução ID `32706985886` (2026-08-24T08:34:19Z): `success`
  - Execução ID `32599777105` (2026-08-22T21:30:18Z): `success`
  - Execução ID `32599641207` (2026-08-22T21:27:30Z): `failure`

### Ingestão Diária - Fact Checking (RSS Multi-Agências)
  - Execução ID `32694222448` (2026-08-24T05:37:59Z): `failure`
  - Execução ID `32620462928` (2026-08-23T05:29:06Z): `failure`

### Ingestão Semanal - TSE (Bens e Financiamentos)
  - Execução ID `32687769008` (2026-08-24T03:49:07Z): `failure`
  - Execução ID `32549426068` (2026-08-22T03:36:09Z): `success`

### Ingestão Diária - Querido Diário (Atos Municipais)
  - Execução ID `32687386230` (2026-08-24T03:42:32Z): `failure`
  - Execução ID `32615908899` (2026-08-23T03:39:43Z): `failure`

### Ingestão Diária - Senado Federal
  - Execução ID `32682950201` (2026-08-24T02:24:21Z): `failure`
  - Execução ID `32612835612` (2026-08-23T02:25:46Z): `failure`
  - Execução ID `32545830880` (2026-08-22T02:17:06Z): `success`

### Ingestão Semanal - TSE DivulgaCandContas (Prestação de Contas)
  - Execução ID `32613898779` (2026-08-23T02:51:45Z): `failure`

### .github/workflows/monitor_and_heal_pipelines.yml
  - Execução ID `32596110566` (2026-08-22T20:14:40Z): `failure`
  - Execução ID `32595632855` (2026-08-22T20:05:05Z): `failure`
  - Execução ID `32595261972` (2026-08-22T19:57:44Z): `failure`
  - Execução ID `32586218209` (2026-08-22T16:56:20Z): `failure`

### Pipeline de Ingestão de Dados (Scraping + RAG)
  - Execução ID `32502981966` (2026-08-21T16:27:06Z): `success`

## Diagnóstico Autônomo de LLM (`[LLM-COMMIT-AND-HEAL]`)
**[Diagnóstico Gemini 3.6 Flash (Auto-Curado via Tool Calling)]**
- **Tool Invocada:** `apply_file_patch` em `.github/workflows/ingest_diario_factchecking.yml` -> Resultado: Sucesso: Arquivo .github/workflows/ingest_diario_factchecking.yml curado fisicamente.
