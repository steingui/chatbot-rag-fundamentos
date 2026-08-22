[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]
# Relatório Autônomo de Monitoramento e Auto-Cura

**Status Pinecone:** `OK` | **Total Vetores:** 1153

## Auditoria e Auto-Cura de Documentos Local (`data/docs`)
- **Total de Arquivos:** 0
- **Arquivos Auto-Corrigidos:** 0
- **Arquivos Purgados (Inválidos/Vazios):** 0

## Últimas 5 Execuções por Pipeline de Ingestão (GitHub Actions)
### Monitoramento Autônomo e Auto-Cura de Ingestões
  - Execução ID `32596927464` (2026-08-22T20:31:32Z): `in_progress`
  - Execução ID `32596001974` (2026-08-22T20:12:27Z): `success`
  - Execução ID `32595939298` (2026-08-22T20:11:11Z): `success`
  - Execução ID `32595140657` (2026-08-22T19:55:17Z): `success`
  - Execução ID `32594871941` (2026-08-22T19:49:53Z): `failure`

### .github/workflows/monitor_and_heal_pipelines.yml
  - Execução ID `32596110566` (2026-08-22T20:14:40Z): `failure`
  - Execução ID `32595632855` (2026-08-22T20:05:05Z): `failure`
  - Execução ID `32595261972` (2026-08-22T19:57:44Z): `failure`
  - Execução ID `32586218209` (2026-08-22T16:56:20Z): `failure`

### Ingestão Diária - Câmara dos Deputados
  - Execução ID `32595951013` (2026-08-22T20:11:25Z): `success`
  - Execução ID `32590150369` (2026-08-22T18:14:25Z): `success`
  - Execução ID `32583973239` (2026-08-22T16:11:42Z): `success`
  - Execução ID `32577980083` (2026-08-22T14:11:42Z): `success`
  - Execução ID `32572616606` (2026-08-22T12:18:05Z): `success`

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
**[Diagnóstico Gemini 3.6 Flash]**
### Diagnóstico de CI/CD

**Análise da Falha:**
* **Workflow:** `Monitoramento Autônomo e Auto-Cura de Ingestões` (`.github/workflows/monitor_and_heal_pipelines.yml`)
* **Etapa com Falha:** `Create Pull Request with Auto-Healed Fixes & Health Report`
* **Causa Raiz:** A ação `peter-evans/create-pull-request@v6` falhou ao tentar criar a branch `auto-heal/pipeline-fix` e abrir o Pull Request autônomo. Isso ocorre quando o `GITHUB_TOKEN` padrão do repositório não possui privilégios de criação e aprovação de Pull Requests habilitados nas configurações da organização/repositório do GitHub.

---

### Ações Recomendadas para Resolução (Painel do GitHub):

1. **Habilitar Permissões de Pull Request em Actions:**
   * Acesse no repositório: **Settings** $\rightarrow$ **Actions** $\rightarrow$ **General**.
   * Em **Workflow permissions**, selecione **Read and write permissions**.
   * Marque a caixa de seleção **"Allow GitHub Actions to create and approve pull requests"**.
   * Clique em **Save**.

2. **Configuração de Token Personalizado (Opcional):**
   * Caso o repositório pertença a uma organização com políticas restritas de `GITHUB_TOKEN`, configure o Secret `GH_TOKEN` em **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions** contendo um Personal Access Token (PAT) com os escopos `repo` e `workflow`.

---
*Nota: Nenhuma alteração no código fonte foi realizada, em conformidade com os guardrails de segurança de sintaxe e permissões dos workflows de CI/CD.*
