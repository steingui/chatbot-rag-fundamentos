# 🗺️ Roadmap do Projeto (Próximos Passos)

A arquitetura base de Backend e Ingestão está **100% funcional, automatizada e em produção**. O foco de amanhã será expandir a experiência do usuário e a inteligência dos dados.

## Fase 0: Arquitetura Base (Concluído ✅)
- [x] Criar scripts de scraping modulares (`scraper_camara.py`, etc) para extrair dados.
- [x] Refatorar scraper para injetar metadados diretamente no chunk (contexto robusto).
- [x] Construir módulo centralizado de Ingestão (`pinecone_ingestor.py`) utilizando Pinecone e Embeddings HuggingFace.
- [x] Automatizar a Ingestão via GitHub Actions (Cron Job 2x ao dia).
- [x] Construir Backend em FastAPI para expor o LangChain e a lógica do RAG.
- [x] Deploy da API no Render (Serverless) conectado ao OpenRouter (Llama 3 / Modelos Free).

## Fase 1: Interface de Usuário (Frontend)
- [ ] Criar interface gráfica (UI) para o Chatbot.
- [ ] **Opções de Stack:** 
  - *Opção A:* **Streamlit** (Deploy super rápido em Python, focado em dados).
  - *Opção B:* **Vanilla HTML/CSS/JS** ou **Next.js** (Design UI/UX premium, animações e responsividade).
- [ ] Conectar o frontend diretamente ao endpoint `/chat` do Render.

## Fase 2: RAG Avançado e Qualidade de Dados
- [ ] **Evolução do Scraper (Foco Eleições 2026):**
  - **Planos de Governo (TSE):** Extrair PDFs/textos das propostas de candidatos e aplicar uma etapa de "Refinamento" via LLM (limpeza e formatação) antes da ingestão. *(Esqueleto Criado ✅)*
  - **Fact-Checking:** Coletar feeds RSS de agências (Lupa, Aos Fatos) para cruzar discursos com checagens estruturadas no Pinecone (reduzindo alucinações). *(Esqueleto Criado ✅)*
  - **Financiamento e Bens:** Capturar evolução patrimonial e doadores de campanha na API do TSE. *(Esqueleto Criado ✅)*
- [x] **Enriquecimento das Votações:** Buscar a "Ementa" (resumo do que trata a lei/proposição) na API da Câmara, para ir além da sigla fria (ex: "PEC 45/2019").
- [x] **Memória de Conversação:** Adicionar `ConversationBufferMemory` no LangChain para que o bot lembre de perguntas anteriores na mesma sessão.
- [x] **Citação de Fontes:** Modificar o RAG para retornar os metadados (links, sessões ou IDs) de onde a IA tirou a resposta.

## Fase 3: Monitoramento e CI/CD Final
- [ ] Deploy automático do Frontend.
- [ ] Testes de validação da saúde do banco de vetores Pinecone.
- [ ] (Opcional) Guardar logs das perguntas mais frequentes para análise de interesse.

## Fase 4: Melhorias Futuras (Visão a Longo Prazo)
- [ ] **Hybrid Search no Pinecone:** Misturar busca semântica (vetorial) com busca léxica (palavras-chave via BM25) para aumentar a precisão de buscas por nomes exatos de deputados ou siglas muito específicas.
- [ ] **Agentes (Tool Calling):** Evoluir o LangChain de uma "Chain" simples para um "Agent". O bot poderia ter ferramentas para, por exemplo, buscar notícias em tempo real na web ou consultar gráficos.
- [ ] **Banco de Dados Relacional:** Adicionar um PostgreSQL para salvar o perfil de cada deputado, permitindo respostas analíticas precisas (ex: "Quantas vezes o deputado X votou Sim neste ano?") sem depender de matemática via LLM (que costuma falhar).
- [ ] **Autenticação:** Sistema de login para que usuários possam salvar seus históricos de chat e criar alertas de votações.

---
*Status Atual: Backend Operacional | Cron Job: 2x/dia | Vector DB: Pinecone*
