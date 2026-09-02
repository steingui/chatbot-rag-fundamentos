# ☁️ Backlog 04: Infraestrutura, GCP & Deploy Serverless

> **Objetivo:** Unificar toda a infraestrutura no Google Cloud Platform (GCP) com arquitetura 100% on-demand (custo zero em inatividade).

---

## 🎯 Tarefas & Histórias de Usuário

### 4.1 Consolidação GCP Serverless
- [x] **[INF-401]** Containerizar aplicação backend FastAPI para execução no GCP Cloud Run (`Dockerfile`).
- [ ] **[INF-402]** Mapear variáveis de ambiente locais para o GCP Secret Manager (substituindo arquivos `.env` em produção).
- [ ] **[INF-403]** Configurar Firestore NoSQL na região `southamerica-east1` (São Paulo) com regras de acesso e índices.
- [ ] **[INF-404]** Configurar mapeamento de domínio customizado (`api.politichat.com.br`) no Cloud Run com SSL automático.

### 4.2 CI/CD & Automação de Builds
- [x] **[INF-405]** Configurar pipeline no GCP Cloud Build (`cloudbuild.yaml`) para deploy automático da API a cada push na branch `main`.
- [ ] **[INF-406]** Configurar GitHub Actions para builds automatizados do app mobile via Expo Application Services (EAS Build).
- [ ] **[INF-407]** Configurar monitoramento e observabilidade via GCP Cloud Logging, Error Reporting e Cloud Trace.
