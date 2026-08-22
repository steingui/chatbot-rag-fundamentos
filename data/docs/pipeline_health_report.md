[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]
# Relatório Autônomo de Monitoramento e Auto-Cura

**Status Pinecone:** `OK` | **Total Vetores:** 1153

## Auditoria e Auto-Cura de Documentos Local (`data/docs`)
- **Total de Arquivos:** 0
- **Arquivos Auto-Corrigidos:** 0
- **Arquivos Purgados (Inválidos/Vazios):** 0

## Últimas 5 Execuções por Pipeline de Ingestão (GitHub Actions)
### Monitoramento Autônomo e Auto-Cura de Ingestões
  - Execução ID `32593772462` (2026-08-22T19:27:43Z): `in_progress`
  - Execução ID `32590200068` (2026-08-22T18:15:25Z): `failure`
  - Execução ID `32586304445` (2026-08-22T16:58:06Z): `failure`
  - Execução ID `32585674287` (2026-08-22T16:45:32Z): `success`
  - Execução ID `32585253159` (2026-08-22T16:37:13Z): `success`

### Ingestão Diária - Câmara dos Deputados
  - Execução ID `32590150369` (2026-08-22T18:14:25Z): `success`
  - Execução ID `32583973239` (2026-08-22T16:11:42Z): `success`
  - Execução ID `32577980083` (2026-08-22T14:11:42Z): `success`
  - Execução ID `32572616606` (2026-08-22T12:18:05Z): `success`
  - Execução ID `32567018717` (2026-08-22T10:12:47Z): `success`

### .github/workflows/monitor_and_heal_pipelines.yml
  - Execução ID `32586218209` (2026-08-22T16:56:20Z): `failure`

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
A etapa `Create Pull Request with Auto-Healed Fixes & Health Report` falhou na Action `peter-evans/create-pull-request@v6` devido a restrições de permissão do token padrão `GITHUB_TOKEN` em execuções engatilhadas por `workflow_run`. Por padrão, o GitHub bloqueia a criação de Pull Requests via `GITHUB_TOKEN` a menos que a opção *"Allow GitHub Actions to create and approve pull requests"* esteja ativada nas configurações do repositório, ou um Personal Access Token (`GH_TOKEN` / `PAT`) seja fornecido com permissões explícitas de gravação e automação.

---

### Correção

#### 1. `.github/workflows/monitor_and_heal_pipelines.yml`
Atualize a chave `token` da etapa para aceitar um PAT customizado (`GH_TOKEN`) com fallback para `GITHUB_TOKEN`, e garanta a configuração prévia da identidade do Git:

```yaml
<<<<
      - name: Create Pull Request with Auto-Healed Fixes & Health Report
        if: steps.audit.outputs.should_commit == 'true'
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "[LLM-AUTOCURE] fix(ingestion): auto-heal data quality & pipeline health report"
          branch: auto-heal/pipeline-fix
          title: "[LLM-AUTOCURE] Diagnóstico e Correção Autônoma de Ingestão"
          body-path: 'data/docs/pipeline_health_report.md'
          labels: 'autocure, pipeline-health'
          delete-branch: true
====
      - name: Configure Git Identity
        if: steps.audit.outputs.should_commit == 'true'
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"

      - name: Create Pull Request with Auto-Healed Fixes & Health Report
        if: steps.audit.outputs.should_commit == 'true'
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{ secrets.GH_TOKEN || secrets.GITHUB_TOKEN }}
          commit-message: "[LLM-AUTOCURE] fix(ingestion): auto-heal data quality & pipeline health report"
          branch: auto-heal/pipeline-fix
          title: "[LLM-AUTOCURE] Diagnóstico e Correção Autônoma de Ingestão"
          body-path: 'data/docs/pipeline_health_report.md'
          labels: 'autocure, pipeline-health'
          delete-branch: true
>>>>
```

#### 2. Configuração Manual Recomendada no GitHub (Repositório)
No seu repositório do GitHub, navegue até:
**Settings** > **Actions** > **General** > **Workflow permissions**  
Marque a opção: **"Allow GitHub Actions to create and approve pull requests"** e salve.
