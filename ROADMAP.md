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
- [x] Criar interface gráfica (UI) para o Chatbot (Vite + React com estética terminal monospace em produção no Render).
- [x] Conectar o frontend diretamente ao endpoint `/chat` do Render com suporte a multi-sessão e sugestões rápidas de prompt.

## Fase 2: RAG Avançado e Qualidade de Dados
- [x] **Evolução do Scraper (Foco Eleições 2026):**
  - [x] **Planos de Governo (TSE):** Extrair PDFs/textos das propostas de candidatos e aplicar uma etapa de "Refinamento" via LLM (limpeza e formatação) antes da ingestão. *(Finalizado ✅)*
  - [x] **Fact-Checking:** Coletar feeds RSS de agências (Lupa, Aos Fatos) para cruzar discursos com checagens estruturadas no Pinecone (reduzindo alucinações). *(Finalizado ✅)*
  - [x] **Financiamento e Bens:** Capturar evolução patrimonial e doadores de campanha na API do TSE. *(Finalizado ✅)*
- [x] **Enriquecimento das Votações:** Buscar a "Ementa" (resumo do que trata a lei/proposição) na API da Câmara, para ir além da sigla fria (ex: "PEC 45/2019").
- [x] **Memória de Conversação:** Adicionar `ConversationBufferMemory` no LangChain para que o bot lembre de perguntas anteriores na mesma sessão.
- [x] **Citação de Fontes:** Modificar o RAG para retornar os metadados (links, sessões ou IDs) de onde a IA tirou a resposta.

## Fase 3: Monitoramento, Infraestrutura e CI/CD Final
- [ ] **Otimização de Latência e Limites (PaaS):**
  - Configurar **UptimeRobot** no endpoint do Render (evita *Cold Starts* de 50s no plano Free).
  - Configurar *Keep-Alive* contínuo para o endpoint de Embeddings da Hugging Face.
  - Habilitar **Provider Routing (Fallbacks)** ou configurar **BYOK (Bring Your Own Key)** do Google AI Studio no OpenRouter para mitigar gargalos (Rate Limit 429).
- [x] Deploy automático do Frontend (Vite/React) via Blueprint do Render.
- [ ] Testes de validação da saúde do banco de vetores Pinecone.
- [ ] (Opcional) Guardar logs das perguntas mais frequentes para análise de interesse.

## Fase 4: Melhorias Futuras (Visão a Longo Prazo)
- [ ] **Hybrid Search no Pinecone:** Misturar busca semântica (vetorial) com busca léxica (palavras-chave via BM25) para aumentar a precisão de buscas por nomes exatos de deputados ou siglas muito específicas.
- [x] **Agentes (Tool Calling):** Evoluir o LangChain de uma "Chain" simples para um **ReAct Agent**. O bot consulta em tempo real a base vetorial do Pinecone e a web via DuckDuckGo Search, unificando e sintetizando as fontes. *(Finalizado ✅)*
- [ ] **Banco de Dados Relacional:** Adicionar um PostgreSQL para salvar o perfil de cada deputado, permitindo respostas analíticas precisas (ex: "Quantas vezes o deputado X votou Sim neste ano?") sem depender de matemática via LLM (que costuma falhar).
- [ ] **Autenticação:** Sistema de login para que usuários possam salvar seus históricos de chat e criar alertas de votações.

## Fase 5: Expansão de Fontes de Dados Abertos
- [ ] **API do Senado Federal (`legis.senado.leg.br`):** Scraper e ingestor para proposições, votações, discursos dos senadores e uso da CEAPS (Cota Parlamentar).
- [ ] **API do Portal da Transparência / CGU (`portaldatransparencia.gov.br`):** Rastreador de emendas parlamentares (individuais/PIX) e execução orçamentária por deputado/senador.
- [ ] **Querido Diário (Open Knowledge Brasil):** Conectar à API de Diários Oficiais Municipais para monitorar atos, nomeações e licitações locais.
- [ ] **API REST do TSE (DivulgaCandContas):** Ingestão detalhada de prestação de contas de campanha por CPF/CNPJ de doadores e fornecedores.
- [ ] **Feeds RSS de Checagem Adicionais:** Parser de feeds RSS de agências adicionais (*Aos Fatos*, *Estadão Verifica*, *Agência Pública*).

---
*Status Atual: Backend & Agente ReAct Operacionais | Frontend React Ativo | Vector DB: Pinecone*
