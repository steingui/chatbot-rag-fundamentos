# 📱 Roadmap Mobile — Discovery para App Store & Google Play

> **Projeto:** Chatbot RAG Político (Transparência Legislativa Brasileira)
> **Objetivo:** Publicar um app mobile nativo com UX premium nas lojas Apple e Google.
> **Data:** Agosto 2026

---

## 1. Modelos de IA: Free vs. Investimento para MVP

### Estado Atual (Free Tier — OpenRouter)

| Componente | Modelo Atual | Tier | Limitação Crítica |
|---|---|---|---|
| **LLM Principal** | `google/gemma-4-31b-it:free` | Free | Rate limit 20 RPM, instabilidade, sem SLA |
| **Fallback 1** | `nvidia/nemotron-3.5-lightning:free` | Free | Disponibilidade errática, sem garantia |
| **Fallback 2** | `minimax/minimax-m3:free` | Free | Qualidade inferior em pt-BR |
| **Embedding** | `sentence-transformers/all-MiniLM-L6-v2` (HF) | Free | Modelo genérico inglês, 384 dims, limitado em pt-BR |
| **Reranker** | `bge-reranker-v2-m3` (Pinecone) | Incluso | Funcional, boa relação custo-benefício |

### Diagnóstico

Modelos free **não têm SLA**, sofrem rate-limiting agressivo (HTTP 429), e são descontinuados sem aviso — inviáveis para app publicado em loja com expectativa de disponibilidade.

### Recomendação para MVP Mobile (Custo Mínimo Viável)

A estratégia é **maximizar free tiers** e usar modelos pagos ultra-baratos apenas como fallback.

| Componente | Modelo Recomendado | Custo/mês | Justificativa |
|---|---|---|---|
| **LLM Principal** | `gemini-3.7-flash` (Google AI Studio — Free Tier) | **$0** (free até rate limit) | Free tier generoso, bom pt-BR, streaming, sem custo enquanto cabe no rate limit |
| **LLM Fallback 1** | `llama-3.3-70b` via **Groq** (Free Tier) | **$0** (free) | Latência ultra-baixa (LPU), free tier sem cartão, excelente fallback |
| **LLM Fallback 2** | `deepseek-v4-flash` via OpenRouter/API direta | **~$1-3** | $0.14/1M input tokens — absurdamente barato, bom raciocínio |
| **LLM Pago (burst)** | `gemini-3.7-flash` (Google — Paid Tier) | **~$2-5** | $0.75/1M input (promo até dez/2026), só ativa quando free estoura |
| **Embedding** | `sentence-transformers/all-MiniLM-L6-v2` (manter) | **$0** | Funcional para MVP. Migrar para multilíngue na v2 |
| **Reranker** | `bge-reranker-v2-m3` (Pinecone nativo — manter) | **Incluso** | Já compensa limitação do embedding com reranking |
| **Web Search** | `ddgs` (manter) | **$0** | Funcional, sem custo |

### Estratégia de Roteamento Econômico

```
Usuário envia mensagem
  │
  ├─→ Tenta Gemini 3.7 Flash (Free Tier)
  │     └─ Se 429 (rate limit) ou erro:
  │
  ├─→ Tenta Groq Llama 3.3 70B (Free Tier)
  │     └─ Se 429 ou erro:
  │
  ├─→ Tenta DeepSeek V4 Flash ($0.14/1M tokens)
  │     └─ Se falha total:
  │
  └─→ Gemini 3.7 Flash (Paid Tier — $0.75/1M tokens)
```

**Custo estimado LLM para 10k mensagens/mês: $0 a $5** (maioria absorvida pelos free tiers).

### Plano de Migração de Modelos

```
Fase 1 (MVP): Trocar OpenRouter → Google AI Studio (Gemini) + Groq + DeepSeek diretos
Fase 2 (MVP): Manter embedding atual (MiniLM) — reranker compensa
Fase 3 (v2):  Re-indexar com multilingual-e5-large quando validar PMF
Fase 4 (v2):  Avaliar gpt-4o-mini ou Claude Haiku se receita justificar
```

**Sobre o Embedding**: o `all-MiniLM-L6-v2` é limitado em pt-BR, mas o reranker `bge-reranker-v2-m3` já corrige boa parte do ruído. Para MVP, não vale o custo de re-ingestão. Migrar para `multilingual-e5-large` (Pinecone nativo, incluso) na v2 quando tiver product-market fit.

---

## 2. Backend: O Que Precisa Mudar para Sustentar App

### Gaps Atuais

| Área | Estado Atual | Risco para Mobile |
|---|---|---|
| **Autenticação** | Nenhuma | Qualquer pessoa acessa a API aberta |
| **Rate Limiting** | IP-based (slowapi) | Não funciona bem com mobile (NAT/carrier) |
| **Persistência** | Sem banco de dados | Histórico perdido ao reiniciar, sem perfil de usuário |
| **Push Notifications** | Inexistente | Impossível alertar sobre novos dados legislativos |
| **Deploy** | Render Free (sleep after 15min) | Latência de cold-start de ~30s, inaceitável para mobile |
| **Observabilidade** | Logging básico | Sem métricas de uso, crash reports, ou analytics |

### Melhorias Obrigatórias (Pré-Launch)

#### 2.1 Autenticação & Autorização
```
Stack recomendada:
├── Firebase Auth (Google/Apple Sign-In) — SDK nativo mobile
├── JWT Bearer tokens na API FastAPI
└── Middleware de validação por token (substituir OriginCheckMiddleware)
```
- Firebase Auth é gratuito até 10k MAU e integra nativamente com iOS/Android
- Backend valida o `id_token` do Firebase, extrai `uid` do usuário
- Elimina a necessidade de gerenciar senhas, OAuth flows, etc.

#### 2.2 Banco de Dados (PostgreSQL)
```
Tabelas essenciais:
├── users (uid, name, email, created_at, plan_tier)
├── conversations (id, user_id, title, created_at)
├── messages (id, conversation_id, role, content, model_used, tokens, created_at)
├── user_preferences (user_id, theme, notifications_enabled)
└── usage_metrics (user_id, date, query_count, tokens_consumed)
```
- Usar **Supabase** (PostgreSQL gerenciado + auth alternativo) ou **Neon** (serverless Postgres, free tier generoso)
- ORM: `SQLAlchemy 2.0` async com `asyncpg`

#### 2.3 Rate Limiting por Usuário
```python
# Substituir IP-based por user-based
# Plano Free:  10 msgs/dia
# Plano Pro:   100 msgs/dia
# Plano Premium: ilimitado
```

#### 2.4 Push Notifications
- **Firebase Cloud Messaging (FCM)** — gratuito, suporte iOS + Android
- Worker background (já existe `backend/workers/`) registra novos dados ingeridos e dispara notificação

#### 2.5 API Versionada
```
/api/v1/chat          → contrato atual
/api/v1/chat/stream   → SSE streaming
/api/v1/auth/token     → troca Firebase token por JWT interno
/api/v1/user/profile   → perfil e preferências
/api/v1/user/history   → histórico paginado
```

---

## 3. App Mobile: Framework & UX

### Escolha de Framework

| Framework | Prós | Contras | Veredicto |
|---|---|---|---|
| **React Native (Expo)** | Reutiliza conhecimento React/TS do frontend atual, ecossistema gigante, Expo simplifica build/deploy | Performance ligeiramente inferior, dependência do bridge | **Recomendado** |
| **Flutter** | Performance nativa, UI consistente cross-platform, Dart performático | Curva de aprendizado (Dart), não reutiliza código React existente | Boa alternativa |
| **Kotlin/Swift nativos** | Máxima performance | 2 codebases, 2x esforço de manutenção | Inviável para MVP |

**React Native com Expo** é a escolha ideal porque:
1. O projeto já usa React + TypeScript + Zustand no frontend web
2. Lógica de estado (stores), chamadas à API, e parsing de markdown podem ser reutilizados
3. Expo oferece build cloud (EAS Build) sem necessidade de Xcode/Android Studio local
4. OTA updates (sem passar pela revisão da loja para correções)

### Stack Mobile Proposta

```
React Native (Expo SDK 52+)
├── Navigation:     expo-router (file-based, como Next.js)
├── State:          zustand (reutilizar stores do web)
├── UI Kit:         React Native Paper ou Tamagui (design system premium)
├── Markdown:       react-native-markdown-display
├── Auth:           @react-native-firebase/auth
├── Push:           expo-notifications + FCM
├── Streaming:      EventSource polyfill (react-native-sse)
├── Storage:        expo-secure-store (tokens), AsyncStorage (prefs)
└── Analytics:      Firebase Analytics / PostHog
```

### Diretrizes de UX Mobile (Não é Port do Web)

1. **Chat-first**: Tela principal é a conversa, sem sidebar — usar bottom sheet para sessões
2. **Quick Actions**: Sugestões como chips deslizáveis acima do teclado (não cards grandes)
3. **Haptic Feedback**: Vibração sutil ao receber resposta, copiar texto, trocar sessão
4. **Skeleton Loading**: Animação de "typing indicator" ao aguardar LLM
5. **Deep Links**: `politichat://chat?q=gastos+deputado+X` para compartilhamento
6. **Offline Mode**: Cache local com SQLite (expo-sqlite) para reler conversas sem rede
7. **Dark/Light**: Seguir tema do sistema, com override manual
8. **Fontes**: Inter ou SF Pro (iOS) / Roboto (Android) via sistema

### Telas Principais

```
Tela 1: Onboarding (3 slides → valor do app → Sign In with Google/Apple)
Tela 2: Chat Principal (bolhas com markdown renderizado, fontes citadas inline)
Tela 3: Drawer de Sessões (swipe para deletar, badge de novas notificações)
Tela 4: Perfil & Assinatura (uso do mês, upgrade de plano)
```

---

## 4. Deploy & Domínio — Estratégia GCP-First

### Por Que Consolidar Tudo no Google Cloud?

O projeto já depende de vários serviços Google (Gemini LLM, Firebase Auth, FCM, Analytics). Consolidar **toda a infra no GCP** gera ganhos concretos:

| Ganho | Impacto |
|---|---|
| **Billing único** | Uma fatura, um dashboard, um cartão |
| **Zero egress interno** | Tráfego entre Cloud Run ↔ Firestore ↔ Firebase = $0 (mesma região) |
| **IAM unificado** | Service accounts falam entre si nativamente, sem gerenciar API keys extras |
| **Secret Manager** | Substitui `.env` files — secrets versionados, auditados, rotação automática |
| **Domínio nativo** | Cloud Run mapeia custom domain com SSL automático (sem Cloudflare) |
| **Menos vendors** | Menos contas, menos dashboards, menos pontos de falha |
| **Observabilidade grátis** | Cloud Logging + Cloud Trace + Error Reporting inclusos |

### Stack GCP Completa (Tudo On-Demand)

```
Google Cloud Platform (região: southamerica-east1 — São Paulo)
│
├── Cloud Run (Backend API)
│   ├── Dockerfile atual funciona direto
│   ├── Scale-to-zero (min-instances=0)
│   ├── Free: 2M req/mês, 180k vCPU-sec, 360k GB-sec
│   └── Custo MVP: $0
│
├── Firestore (Banco de Dados)
│   ├── NoSQL serverless, scale-to-zero
│   ├── Free: 1 GB storage, 50k reads/day, 20k writes/day
│   ├── Perfeito para: users, conversations, messages, preferences
│   └── Custo MVP: $0
│
├── Gemini API (LLM Principal)
│   ├── gemini-3.7-flash via Vertex AI ou AI Studio
│   ├── Free tier generoso (rate-limited)
│   ├── Paid: $0.75/1M input tokens (promo até dez/2026)
│   └── Custo MVP: $0-5
│
├── Firebase (Auth + Push + Analytics)
│   ├── Auth: Google/Apple Sign-In, 10k MAU grátis
│   ├── FCM: Push notifications ilimitadas grátis
│   ├── Analytics: eventos ilimitados grátis
│   └── Custo MVP: $0
│
├── Secret Manager (Secrets)
│   ├── Substitui .env — versionado, auditado
│   ├── Free: 6 secret versions ativas
│   └── Custo MVP: $0
│
├── Cloud Build (CI/CD)
│   ├── Free: 120 min/dia de build
│   ├── Deploy automático no push to main
│   └── Custo MVP: $0
│
├── Artifact Registry (Docker Images)
│   ├── Free: 500 MB storage
│   └── Custo MVP: $0
│
└── Cloud CDN + Load Balancer (opcional, v2)
    └── Para quando precisar de latência <100ms global
```

### Serviços que Ficam Fora do GCP

| Serviço | Razão |
|---|---|
| **Pinecone** (Vector DB) | Free tier superior ao Vertex AI Vector Search. Manter até escalar |
| **Groq** (LLM Fallback) | LPU proprietário, sem equivalente GCP. Fallback externo |
| **DeepSeek** (LLM Fallback) | Ultra-barato, sem equivalente GCP no preço |
| **DuckDuckGo** (Web Search) | API gratuita, sem custo |

### Firestore vs PostgreSQL (Neon) — Por Que Firestore no MVP

| Aspecto | Firestore | Neon (Postgres) |
|---|---|---|
| Setup | Zero config, SDK Firebase direto | Precisa SQLAlchemy, migrations |
| Scale-to-zero | Nativo | Sim, com auto-suspend |
| Free tier | 1 GB, 50k reads/dia | 0.5 GB |
| Integração Firebase | Nativa (rules, auth, triggers) | Requer middleware |
| Consultas complexas | Limitado (NoSQL) | SQL completo |
| Migração futura | Exporta para BigQuery se precisar | — |

**Para MVP (chat history + user prefs)**: Firestore é mais simples e integra nativamente com Firebase Auth. Se precisar de queries SQL complexas (analytics, relatórios), migrar para Cloud SQL/AlloyDB na v2.

### Domínio Próprio
```
Registrar: politichat.com.br (Registro.br ~R$40/ano)
Subdomínios:
├── api.politichat.com.br   → Cloud Run (custom domain mapping, SSL automático)
├── app.politichat.com.br   → Firebase Hosting (frontend web/PWA)
└── (sem CDN separado — Cloud Run já serve com edge caching)
```

### CI/CD Unificado
```yaml
# Cloud Build (trigger no push to main)
steps:
  - build Docker image → Artifact Registry
  - deploy → Cloud Run (zero downtime)

# GitHub Actions (mobile — EAS Build)
  - build Android (AAB) + iOS (IPA)
  - expo eas submit → App Store Connect + Google Play Console
```

---

## 5. Publicação nas Lojas

### Requisitos Apple App Store

| Item | Ação | Custo |
|---|---|---|
| Apple Developer Program | Conta de desenvolvedor | $99/ano |
| App Review Guidelines | Conformidade com seções 4.2 (design mínimo) e 5.1 (privacidade) | — |
| Política de Privacidade | Criar página em `politichat.com.br/privacidade` | — |
| App Tracking Transparency | Implementar diálogo ATT se usar analytics com tracking | — |
| In-App Purchase | Obrigatório para assinaturas digitais (Apple cobra 30%) | 30% da receita |

### Requisitos Google Play Store

| Item | Ação | Custo |
|---|---|---|
| Google Play Console | Conta de desenvolvedor | $25 (único) |
| Data Safety Form | Declarar dados coletados/compartilhados | — |
| Content Rating | Classificação IARC (preencher questionário) | — |
| Target Audience | Declarar 18+ (conteúdo político) | — |

### Checklist Pré-Submissão
- [ ] Política de Privacidade (LGPD compliance)
- [ ] Termos de Uso
- [ ] Ícone do app (1024x1024)
- [ ] Screenshots para cada dispositivo (iPhone 6.7", 6.5", iPad, Android phone/tablet)
- [ ] Vídeo de preview (opcional, mas recomendado)
- [ ] Testes em dispositivos reais (iOS + Android)
- [ ] Crash-free rate > 99.5%

---

## 6. Monetização

### Modelo Recomendado: Freemium + Assinatura

```
┌─────────────┬──────────────────────┬────────────────────────┬─────────────────────┐
│             │ Free                 │ Pro (R$14.90/mês)      │ Premium (R$29.90)   │
├─────────────┼──────────────────────┼────────────────────────┼─────────────────────┤
│ Mensagens   │ 10/dia               │ 100/dia                │ Ilimitado           │
│ Modelo LLM  │ Flash (mais rápido)  │ gpt-4o-mini            │ gpt-4o / Claude 3.5 │
│ Histórico   │ 7 dias               │ 90 dias                │ Ilimitado           │
│ Sessões     │ 1                    │ 5                      │ Ilimitadas          │
│ Notificações│ ❌                   │ ✅ Novos projetos lei  │ ✅ + Alertas custom │
│ Export PDF   │ ❌                   │ ✅                     │ ✅                  │
│ Fontes       │ Base interna         │ + Web Search           │ + Análise profunda  │
│ Anúncios     │ Banner discreto      │ ❌                     │ ❌                  │
└─────────────┴──────────────────────┴────────────────────────┴─────────────────────┘
```

### Outras Fontes de Receita

| Canal | Descrição | Potencial |
|---|---|---|
| **B2G (Gov-to-Business)** | Vender versão white-label para assessorias parlamentares | Alto |
| **API as a Service** | Expor a API RAG para jornalistas/pesquisadores (pay-per-query) | Médio |
| **Dados Agregados** | Dashboard de tendências legislativas (analytics) por assinatura | Médio |
| **Parcerias Jornalísticas** | Integração com veículos de imprensa como ferramenta de pesquisa | Alto |
| **Doações / Crowdfunding** | Plataforma civic-tech com apoio da comunidade | Médio |

### Projeção de Custos Operacionais (MVP — Stack GCP-First)

| Item | Custo/mês | Vendor |
|---|---|---|
| Gemini 3.7 Flash (free tier + burst pago) | $0-5 | GCP |
| Groq + DeepSeek (LLM fallbacks on-demand) | $0-2 | Externo |
| Cloud Run (backend serverless) | $0 | GCP |
| Firestore (banco on-demand) | $0 | GCP |
| Firebase Auth + FCM + Analytics | $0 | GCP |
| Secret Manager + Cloud Build + Artifact Registry | $0 | GCP |
| Pinecone (vector DB) | $0 | Externo |
| Domínio (.com.br) | ~R$3.50 | Registro.br |
| Apple Developer | ~$8.25 | Apple |
| **Total estimado** | **~$8-15/mês (~R$40-80)** | |

**Billing unificado**: GCP + Firebase = uma única fatura Google. Apenas Pinecone, Groq e Apple são vendors separados.
**Se zero tráfego, custo ≈ $8/mês** (apenas domínio + Apple Dev). Tudo escala on-demand.
Com **5 assinantes Pro** (R$14.90), o app já se paga.

---

## 7. Cronograma Sugerido

| Fase | Duração | Entregas |
|---|---|---|
| **Fase 1: Backend Hardening** | 2 semanas | Auth (Firebase), PostgreSQL, rate-limit por user, API versionada |
| **Fase 2: Migração de Modelos** | 1 semana | LLM pago, re-indexar embeddings multilíngue, benchmark |
| **Fase 3: App Mobile (MVP)** | 4 semanas | Chat, auth, streaming, sessões, dark mode, offline cache |
| **Fase 4: Deploy & Domínio** | 1 semana | Domínio, SSL, CI/CD, Render Starter |
| **Fase 5: Monetização** | 1 semana | In-app purchase (RevenueCat), tiers, paywall |
| **Fase 6: Submissão às Lojas** | 1-2 semanas | Screenshots, review, compliance LGPD, publish |
| **Total** | **~10-12 semanas** | App publicado e monetizado |

---

## 8. Decisões Pendentes (Precisam de Input)

1. **Nome do app**: "PolitiChat"? "Legisla AI"? "Transparência IA"?
2. **Apple Developer**: Conta pessoa física ou jurídica (MEI)?
3. **Primeiro modelo pago**: OpenAI (gpt-4o-mini) ou Google (Gemini Flash)?
4. **Banco de dados**: Supabase (mais features) ou Neon (mais simples)?
5. **UI Kit mobile**: React Native Paper (Material) ou Tamagui (custom design system)?
