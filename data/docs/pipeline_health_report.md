[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]
# Relatório Autônomo de Monitoramento e Auto-Cura

**Status Pinecone:** `OK` | **Total Vetores:** 1153

## Auditoria e Auto-Cura de Documentos Local (`data/docs`)
- **Total de Arquivos:** 0
- **Arquivos Auto-Corrigidos:** 0
- **Arquivos Purgados (Inválidos/Vazios):** 0

## Últimas 5 Execuções por Pipeline de Ingestão (GitHub Actions)
### Monitoramento Autônomo e Auto-Cura de Ingestões
  - Execução ID `32584752333` (2026-08-22T16:27:25Z): `in_progress`
  - Execução ID `32584401819` (2026-08-22T16:20:25Z): `success`
  - Execução ID `32584020789` (2026-08-22T16:12:40Z): `success`
  - Execução ID `32582702260` (2026-08-22T15:46:21Z): `failure`
  - Execução ID `32582352990` (2026-08-22T15:39:29Z): `failure`

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
### CAUSA RAIZ

1. **Tentativa de Force Push Bloqueada**: O step `stefanzweifel/git-auto-commit-action@v5` falha ao tentar executar `git push --force` na branch `main` usando o `GITHUB_TOKEN` padrão (`push_options: '--force'`). As políticas de segurança e proteção de branch do GitHub impedem force pushes realizados pelo token padrão da Action.
2. **Execução sem Mudanças (Dirty Check)**: Quando o script `monitor_and_heal.py` não gera alterações reais em `data/docs/pipeline_health_report.md`, o comando de commit tenta forçar o push de uma árvore de trabalho limpa com a flag `--force`, resultando em erro no job.

---

### CORREÇÃO (DIFF / SNIPPET)

Ajuste no arquivo `.github/workflows/monitor_and_heal_pipelines.yml`:

```diff
      - name: Auto-Commit Data Quality & Health Fixes
        if: steps.audit.outputs.should_commit == 'true'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "[LLM-AUTOCURE] fix(ingestion): auto-heal data quality & pipeline health report [skip ci]"
          branch: main
          file_pattern: 'data/docs/pipeline_health_report.md'
-         add_options: '--force'
-         push_options: '--force'
+         skip_dirty_check: false
+         skip_fetch: true
```
