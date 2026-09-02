# ⚙️ Backlog 02: Backend, API & Persistência

> **Objetivo:** Adequar a API FastAPI para suportar clientes mobile nativos, controle de sessão, persistência determinística e escalabilidade serverless.

---

## 🎯 Tarefas & Histórias de Usuário

### 2.1 Struct & Versionamento de API
- [ ] **[BE-201]** Versionar rotas existentes sob o prefixo `/api/v1` (ex: `/api/v1/chat`, `/api/v1/chat/stream`).
- [ ] **[BE-202]** Criar suporte a Server-Sent Events (SSE) nativo para streaming de respostas no mobile (`/api/v1/chat/stream`).
- [ ] **[BE-203]** Implementar endpoint `/api/v1/user/profile` para recuperar preferências e limites do usuário.
- [ ] **[BE-204]** Implementar endpoint paginado `/api/v1/user/history` para listagem e busca de conversas passadas.

### 2.2 Persistência de Dados (Firestore / PostgreSQL)
- [ ] **[BE-205]** Integrar SDK Firestore (GCP Native) para persistência serverless de usuários, conversas e mensagens.
- [ ] **[BE-206]** Projetar esquema NoSQL: coleções `users`, `conversations`, `messages`, `preferences`, `usage_metrics`.
- [ ] **[BE-207]** Implementar camada ORM/Repository abstrata preparando suporte futuro para PostgreSQL (Neon/Cloud SQL).

### 2.3 Gestão de Limites & Workers
- [ ] **[BE-208]** Migrar Rate Limiting de IP-based (`slowapi`) para User-ID-based vinculado ao plano de assinatura (Free/Pro).
- [ ] **[BE-209]** Integrar disparo de notificações FCM via background worker (`backend/workers/`) na ingestão de novos dados legislativos.
