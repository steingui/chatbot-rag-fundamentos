# 🗺️ Roadmap do Projeto (Próximos Passos)

A arquitetura base de Backend e Ingestão está **100% funcional, automatizada e em produção**. O foco de amanhã será expandir a experiência do usuário e a inteligência dos dados.

## Fase 1: Interface de Usuário (Frontend)
- [ ] Criar interface gráfica (UI) para o Chatbot.
- [ ] **Opções de Stack:** 
  - *Opção A:* **Streamlit** (Deploy super rápido em Python, focado em dados).
  - *Opção B:* **Vanilla HTML/CSS/JS** ou **Next.js** (Design UI/UX premium, animações e responsividade).
- [ ] Conectar o frontend diretamente ao endpoint `/chat` do Render.

## Fase 2: RAG Avançado e Qualidade de Dados
- [ ] **Enriquecimento do Scraper:** Buscar a "Ementa" (resumo do que trata a lei/proposição) na API da Câmara, em vez de apenas a sigla (ex: "PEC 45/2019").
- [ ] **Memória de Conversação:** Adicionar `ConversationBufferMemory` no LangChain para que o bot lembre de perguntas anteriores na mesma sessão.
- [ ] **Citação de Fontes:** Modificar o RAG para retornar os metadados (links ou IDs) de onde a IA tirou a resposta, gerando confiabilidade.

## Fase 3: Monitoramento e CI/CD Final
- [ ] Deploy automático do Frontend.
- [ ] Testes de validação da saúde do banco de vetores Pinecone.
- [ ] (Opcional) Guardar logs das perguntas mais frequentes para análise de interesse.

---
*Status Atual: Backend Operacional | Cron Job: 2x/dia | Vector DB: Pinecone*
