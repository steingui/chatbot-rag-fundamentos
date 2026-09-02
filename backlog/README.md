# 📋 Backlog Geral do Projeto (Unificado & Heterogêneo)

Este diretório contém o backlog modularizado e segmentado por domínio técnico e estratégico do projeto **Chatbot RAG Político (Transparência Legislativa)**.

---

## 📁 Estrutura de Módulos do Backlog

| Módulo | Arquivo | Foco Principal | Status |
|---|---|---|---|
| **1. RAG & IA** | [`01-rag-ai.md`](./01-rag-ai.md) | Routing semântico, modelos (Gemini/Groq/DeepSeek), reranking, mitigação de alucinações | 🟡 Em Progresso |
| **2. Backend & API** | [`02-backend-api.md`](./02-backend-api.md) | FastAPI, versionamento v1, Firestore/Postgres, rate limit por usuário, workers | 🔴 Planejado |
| **3. Mobile App** | [`03-mobile-app.md`](./03-mobile-app.md) | React Native (Expo SDK 52), expo-router, Zustand, Haptic, SQLite cache | 🔴 Planejado |
| **4. Infra & GCP** | [`04-infra-gcp.md`](./04-infra-gcp.md) | GCP Cloud Run, Secret Manager, Cloud Build CI/CD, domínio customizado | 🟡 Em Progresso |
| **5. Auth & Segurança** | [`05-auth-security.md`](./05-auth-security.md) | Firebase Auth, JWT validation middleware, LGPD compliance, guardrails | 🔴 Planejado |
| **6. Monetização & Lojas** | [`06-monetization-store.md`](./06-monetization-store.md) | Tiers Freemium/Pro, RevenueCat IAP, checklists App Store & Google Play | 🔴 Planejado |

---

## 🎯 Prioridades Globais (Próxima Sprint / MVP Mobile)

1. **[RAG-01]** Implementar Semantic Router / Fallback Roteado (Gemini 3.7 Flash → Groq → DeepSeek).
2. **[AUTH-01]** Integrar Firebase Auth SDK no backend FastAPI com middleware de validação JWT.
3. **[MOB-01]** Inicializar projeto React Native com Expo SDK 52 + `expo-router` no diretório `/mobile`.
4. **[INFRA-01]** Configurar GCP Secret Manager para gerenciar segredos unificados no Cloud Run.
5. **[MON-01]** Configurar paywalls e limites por tier de usuário (Free: 10 msgs/dia, Pro: 100 msgs/dia).
