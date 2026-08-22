# 🗺️ Roadmap do Projeto (Próximos Passos)

A arquitetura de Backend, Ingestão Multi-Fonte e ReAct Agent está **100% funcional, automatizada com CI/CD, idempotente e em produção no Render**. 

## Fase 0: Arquitetura Base (Concluído ✅)
- [x] Criar scripts de scraping modulares (`scraper_camara.py`, etc) para extrair dados.
- [x] Refatorar scraper para injetar metadados diretamente no chunk (contexto robusto).
- [x] Construir módulo centralizado de Ingestão (`pinecone_ingestor.py`) utilizando Pinecone e Embeddings HuggingFace.
- [x] Automatizar a Ingestão via GitHub Actions (Cron Jobs para Câmara, Senado, TSE e Transparência).
- [x] Construir Backend em FastAPI para expor o LangChain e a lógica do RAG.
- [x] Deploy da API no Render (Serverless) conectado ao OpenRouter (Llama 3 / Nemotron / DeepSeek).

## Fase 1: Interface de Usuário (Frontend) (Concluído ✅)
- [x] Criar interface gráfica (UI) para o Chatbot (Vite + React com estética terminal monospace em produção no Render).
- [x] Conectar o frontend diretamente ao endpoint `/chat` do Render com suporte a multi-sessão e sugestões rápidas de prompt.
- [x] Padronização de Branding: Favicon SVG customizado no estilo terminal (`>_`) e título de página `rag_politico`.

## Fase 2: RAG Avançado e Qualidade de Dados (Concluído ✅)
- [x] **Evolução do Scraper (Foco Eleições 2026):**
  - [x] **Planos de Governo (TSE):** Extrair PDFs/textos das propostas de candidatos e aplicar uma etapa de "Refinamento" via LLM (limpeza e formatação) antes da ingestão.
  - [x] **Fact-Checking:** Coletar feeds RSS de agências (Lupa, Aos Fatos) para cruzar discursos com checagens estruturadas no Pinecone (reduzindo alucinações).
  - [x] **Financiamento e Bens:** Capturar evolução patrimonial e doadores de campanha na API do TSE.
- [x] **Enriquecimento das Votações:** Buscar a "Ementa" (resumo do que trata a lei/proposição) na API da Câmara, para ir além da sigla fria (ex: "PEC 45/2019").
- [x] **Memória de Conversação:** Adicionar suporte a histórico de conversação por sessão (`session_id`).
- [x] **Citação de Fontes:** Modificar o RAG para retornar os metadados (links, sessões ou IDs) de onde a IA tirou a resposta.

## Fase 3: Monitoramento, Infraestrutura e Consistência de Dados (Concluído ✅)
- [x] **Garantia de Consistência e Idempotência no Vector DB:**
  - [x] Geração de IDs determinísticos MD5 por chunk (`source` + `idx` + `hash_content`).
  - [x] Pré-limpeza preventiva no Pinecone (`limpar_vetores_antigos_por_fonte`) via filtro de metadados antes da ingestão para eliminar chunks órfãos e duplicatas.
- [x] **Resiliência contra Rate Limits (HTTP 429) no LLM:**
  - [x] Implementar **Provider Routing com Fallbacks Nativos** (`ChatOpenAI.with_fallbacks`): `Nemotron 30B` -> `Llama 3.3 70B` -> `DeepSeek R1`.
- [x] **Resiliência e Otimização de Busca Web:**
  - [x] Refatorar busca Web com `DDGS().text` e `DDGS().news` em modo regional `br-pt`, evitando falhas de DNS em endpoints terceiros (Wikipedia) e adicionando timeout rigoroso de 5s.
- [x] Deploy automático do Frontend (Vite/React) via Blueprint do Render.
- [x] Otimização de CI/CD: Atualização de GitHub Actions para Node.js `latest` e instalação rápida `--prefer-binary`.

## Fase 4: Expansão de Fontes de Dados Abertos
- [x] **API do Senado Federal (`legis.senado.leg.br`):** Scraper e ingestor para proposições, votações, discursos dos senadores e uso da CEAPS (Cota Parlamentar). *(Concluído ✅)*
- [x] **API do Portal da Transparência / CGU (`portaldatransparencia.gov.br`):** Rastreador de emendas parlamentares (individuais/PIX) e execução orçamentária por deputado/senador com requisições concorrentes (`ThreadPoolExecutor`). *(Concluído ✅)*
- [x] **Querido Diário (Open Knowledge Brasil):** Conectar à API de Diários Oficiais Municipais para monitorar atos, nomeações e licitações locais. *(Concluído ✅)*
- [x] **API REST do TSE (DivulgaCandContas):** Ingestão detalhada de prestação de contas de campanha por CPF/CNPJ de doadores e fornecedores. *(Concluído ✅)*
- [x] **Feeds RSS de Checagem Adicionais:** Parser de feeds RSS de agências adicionais (*Estadão Verifica*, *Agência Pública*, *Aos Fatos*). *(Concluído ✅)*

## Fase 5: Melhorias Futuras (Visão a Longo Prazo)
- [ ] **Hybrid Search no Pinecone:** Misturar busca semântica (vetorial) com busca léxica (palavras-chave via BM25) para aumentar a precisão de buscas por nomes exatos de deputados ou siglas muito específicas.
- [x] **Agentes (Multi-Source Synthesis):** O bot consulta em tempo real a base vetorial do Pinecone e a web via DuckDuckGo Search, unificando e sintetizando as fontes. *(Concluído ✅)*
- [ ] **Banco de Dados Relacional:** Adicionar um PostgreSQL para salvar o perfil de cada deputado, permitindo respostas analíticas precisas (ex: "Quantas vezes o deputado X votou Sim neste ano?") sem depender de matemática via LLM (que costuma falhar).
- [ ] **Autenticação:** Sistema de login para que usuários possam salvar seus históricos de chat e criar alertas de votações.

---
*Status Atual: Agente RAG + Web Operacional | Multi-Fonte (Câmara, Senado, TSE, CGU) | Vector DB Idempotente (Pinecone) | Frontend React Ativo*
