[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]
# Relatório Autônomo de Monitoramento e Auto-Cura

**Status Pinecone:** `OK` | **Total Vetores:** 1153

## Auditoria e Auto-Cura de Documentos Local (`data/docs`)
- **Total de Arquivos:** 0
- **Arquivos Auto-Corrigidos:** 0
- **Arquivos Purgados (Inválidos/Vazios):** 0

## Últimas 5 Execuções por Pipeline de Ingestão (GitHub Actions)
### Monitoramento Autônomo e Auto-Cura de Ingestões
  - Execução ID `32585253159` (2026-08-22T16:37:13Z): `in_progress`
  - Execução ID `32584752333` (2026-08-22T16:27:25Z): `success`
  - Execução ID `32584401819` (2026-08-22T16:20:25Z): `success`
  - Execução ID `32584020789` (2026-08-22T16:12:40Z): `success`
  - Execução ID `32582702260` (2026-08-22T15:46:21Z): `failure`

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
A etapa `Auto-Commit Data Quality & Health Fixes` falha porque o script `pipelines/ingestion/monitor_and_heal.py` não possui um bloco de execução principal (`__name__ == "__main__"`). Como resultado:
1. O relatório `data/docs/pipeline_health_report.md` nunca é gerado/gravado em disco.
2. A variável de saída `should_commit` não é registrada no arquivo `$GITHUB_OUTPUT`, fazendo com que a Action tente manipular arquivos inexistentes ou sem alterações.

---

### Snippet de Correção

Adicione o bloco de execução ao final de `pipelines/ingestion/monitor_and_heal.py`:

```python
if __name__ == "__main__":
    logging.info("Iniciando auditoria e auto-cura...")
    
    # 1. Executa auditoria local e Pinecone
    local_stats = audit_and_heal_local_docs()
    pinecone_stats = audit_pinecone_health()
    
    # 2. Identifica falhas em workflows
    workflow_runs = audit_github_workflows()
    failed_runs = [
        run for runs in workflow_runs.values() 
        for run in runs if run.get("conclusion") == "failure"
    ]
    
    llm_diagnosis = analyze_failures_with_llm(failed_runs)
    
    # 3. Gera e salva o relatório de saúde
    report_md = f"""# Relatório de Saúde das Pipelines
## Status da Base Local
- **Total de Arquivos:** {local_stats['total_files']}
- **Arquivos Corrigidos:** {local_stats['fixed_files']}
- **Arquivos Removidos (Vazios/Corrompidos):** {local_stats['purged_files']}

## Status do Vector DB (Pinecone)
- **Status:** {pinecone_stats.get('status')}
- **Total de Vetores:** {pinecone_stats.get('total_vectors', 0)}

## Diagnóstico LLM
{llm_diagnosis}
"""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_md, encoding="utf-8")
    logging.info(f"Relatório salvo em {REPORT_PATH}")

    # 4. Sinaliza ao GitHub Actions que há alterações a serem commitadas
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        should_commit = local_stats['fixed_files'] > 0 or local_stats['purged_files'] > 0 or REPORT_PATH.exists()
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"should_commit={'true' if should_commit else 'false'}
")
```
