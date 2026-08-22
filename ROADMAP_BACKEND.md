# 🚀 Roadmap de Melhorias Backend - RAG Político

Este documento estabelece o plano estratégico de evolução da infraestrutura do servidor (**FastAPI + LangChain + Pinecone + SQLite/Redis**), focado em **Segurança**, **Performance/Otimização**, **Escalabilidade** e **Manutenibilidade/DX**.

---

## 1. 🛡️ Segurança & Compliance

| Item | Descrição & Ação Técnica | Prioridade | Status |
| :--- | :--- | :---: | :---: |
| **Rate Limiting por IP/Sessão** | Implementar `slowapi` (Redis-backed) nos endpoints `/chat`, `/chat/stream` e `/suggestions` para prevenir ataques de negação de serviço (DoS) e estouro de cota nas APIs parceiras. | `Alta` | ✅ Concluído |
| **Proteção Anti-Prompt Injection** | Adicionar camada de guarda (*Guardrails* / Pydantic Validator) para sanitizar as perguntas dos usuários antes do envio para a LLM, bloqueando instruções maliciosas de alteração de comportamento. | `Alta` | ✅ Concluído |
| **Gestão de Segredos & CI/CD** | Remover referências diretas de chaves no repositório (ex: `TRANSPARENCIA_API_KEY` nos workflows) e configurar `Infisical` ou `GitHub Secrets` com validação de runtime. | `Alta` | ✅ Concluído |
| **Autenticação & JWT** | Introduzir suporte a autenticação por API Key ou token JWT para proteger rotas administrativas e métricas de analytics. | `Média` | ⏳ Pendente |

---

## 2. ⚡ Otimizações & Performance

| Item | Descrição & Ação Técnica | Prioridade | Status |
| :--- | :--- | :---: | :---: |
| **Cache Semanticamente Similar** | Implementar cache semântico em Redis (via `GPTCache` ou similar) para retornar respostas de perguntas frequentes sem refazer inferências na LLM e consultas no Pinecone. | `Alta` | ✅ Concluído |
| **Persistência Externa (PostgreSQL)** | Migrar o banco local `analytics.db` (SQLite) para um serviço gerenciado (Supabase/Neon/PostgreSQL) garantindo persistência duradoura dos contadores entre deploys no Render. | `Alta` | ✅ Concluído |
| **Assincronismo Nativo (Async/Await)** | Refatorar endpoints do FastAPI e chamadas do DuckDuckGo/Pinecone para utilizar `async def` e requisições assíncronas com `httpx`, evitando travamentos do evento principal do Uvicorn. | `Alta` | ✅ Concluído |
| **Compressão e Resposta Gzip** | Adicionar `GZipMiddleware` no FastAPI para reduzir o tamanho dos payloads transmitidos nas consultas legislativas extensas. | `Baixa` | ⏳ Pendente |

---

## 3. 🏗️ Escalabilidade & Arquitetura RAG

| Item | Descrição & Ação Técnica | Prioridade | Status |
| :--- | :--- | :---: | :---: |
| **Retriever Híbrido (Dense + BM25)** | Combinar a busca vetorial densa do Pinecone com busca lexical esparsa (BM25 / Hybrid Search) para melhorar a precisão em termos técnicos e números de proposições legislativas. | `Alta` | ✅ Concluído |
| **Worker Assíncrono de Ingestão** | Separar o pipeline de raspagem e atualização semanal de dados em um serviço de background com Celery/Redis ou GitHub Actions distribuído. | `Média` | ✅ Concluído |
| **Multi-Provider Fallback Dynamic** | Expandir o orquestrador de resiliência a erros 429/500 para alternar dinamicamente entre OpenRouter, Groq e Ollama local caso haja indisponibilidade na rede. | `Média` | ✅ Concluído |
| **Docker Multi-Stage Build** | Otimizar a imagem Docker do backend reduzindo o tamanho final da imagem base com `python:3.11-slim`, desativando cache do pip e separando dependências de dev. | `Média` | ✅ Concluído |

---

## 4. 🧪 Manutenibilidade, Observabilidade & DX

| Item | Descrição & Ação Técnica | Prioridade | Status |
| :--- | :--- | :---: | :---: |
| **Suíte de Testes com Pytest** | Criar testes automatizados com `pytest` e `pytest-asyncio`, mockando chamadas externas ao Pinecone e OpenRouter para garantir estabilidade dos endpoints no CI/CD. | `Alta` | ✅ Concluído |
| **Observabilidade (Sentry & OpenTelemetry)** | Integrar `Sentry` para rastreamento de exceções em tempo real e `Prometheus`/`OpenTelemetry` para monitorar latência de inferência e saúde dos retrievers. | `Média` | ⏳ Pendente |
| **Documentação Interativa OpenAPI** | Enriquecer as descrições dos schemas Pydantic e respostas de erro na documentação Swagger (`/docs`) e ReDoc (`/redoc`). | `Baixa` | ⏳ Pendente |
