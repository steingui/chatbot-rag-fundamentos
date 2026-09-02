# 🗺️ Roadmap Geral do Projeto & Índice de Backlogs

A arquitetura base de Ingestão Multi-Fonte (Câmara, Senado, TSE, CGU), o Vector DB idempotente (Pinecone), o Backend ReAct Agent (GCP Cloud Run), o Frontend v2 (Firebase Hosting) e os estudos de viabilidade Mobile (React Native + Expo) estão funcionais.

Para garantir um desenvolvimento modular e sustentável, o backlog do projeto foi totalmente segmentado em **módulos heterogêneos de backlog** organizados no diretório [`/backlog`](./backlog/README.md).

---

## 📌 Índice do Backlog Segmentado

1. 🧠 **[RAG & IA](./backlog/01-rag-ai.md)**: Mitigação de alucinações, roteamento semântico (`SemanticRouter`), modelos multi-provider (Gemini 3.7 Flash, Groq, DeepSeek) e reranking.
2. ⚙️ **[Backend & API](./backlog/02-backend-api.md)**: API FastAPI v1, streaming SSE, persistência Firestore/PostgreSQL e workers assíncronos.
3. 📱 **[App Mobile](./backlog/03-mobile-app.md)**: App React Native (Expo SDK 52), `expo-router`, UI Design System, Haptic Feedback e cache offline.
4. ☁️ **[Infra & GCP](./backlog/04-infra-gcp.md)**: GCP Cloud Run, Secret Manager, Cloud Build CI/CD e domínio customizado (`politichat.com.br`).
5. 🔒 **[Auth & Segurança](./backlog/05-auth-security.md)**: Firebase Auth (Google/Apple Sign-In), validação de JWT, guardrails e conformidade LGPD.
6. 💰 **[Monetização & Lojas](./backlog/06-monetization-store.md)**: Paywall Freemium/Pro (RevenueCat) e submissão na Apple App Store & Google Play Store.

---

## 📊 Matriz de Priorização das Próximas Sprints

```
          ALTO IMPACTO
              │
    [RAG-102/103]        [MOB-301/305]
    (Migração LLMs)      (MVP React Native)
              │
BAIXO ────────┼──────── HEAVY
ESFORÇO       │        ESFORÇO
              │
    [SEC-501/502]        [MON-601/603]
    (Firebase Auth)      (RevenueCat IAP)
              │
          BAIXO IMPACTO
```

Consulte [`/backlog/README.md`](./backlog/README.md) para detalhes completos e status de execução.
