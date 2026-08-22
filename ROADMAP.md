# 🗺️ Roadmap do Projeto (Próximos Passos e Melhorias)

A arquitetura base de Ingestão Multi-Fonte (Câmara, Senado, TSE, CGU), o Vector DB idempotente (Pinecone), o Backend ReAct Agent e o Frontend estão **funcionais e em produção**. As sugestões dinâmicas (UX) também foram implementadas.

Este documento foca exclusivamente nas melhorias pendentes, priorizando a mitigação de alucinações e o amadurecimento da IA.

---

## 1. Discovery: Otimização da Estratégia de Merge e Mitigação de Alucinações (ReAct Agent + RAG)

**Objetivo:** Eliminar alucinações causadas por excesso de contexto (ex: IA misturando dados de Cota Parlamentar com notícias irrelevantes de Web Search como Carnaval 2026) e melhorar a fluidez conversacional.

### Problemas Atuais:
- O Agente ReAct se confunde ao tentar amalgamar documentos legais extensos com resultados amplos da web, perdendo o isolamento dos fatos.
- **Janela de Contexto:** O histórico de conversa atual precisa ser otimizado para que os prompts subsequentes mantenham uma coerência lógica com a conversa recente, evitando "amnésia" e perda da linha de raciocínio.

### Hipóteses para Validação (Discovery):
- [ ] **A. Roteamento Semântico (Semantic Router) vs. Merge Fixo:** Em vez de enviar as ferramentas de Web e RAG simultaneamente, um classificador inicial decide se a pergunta requer RAG interno, Web Search ou ambos, evitando poluir o contexto.
- [ ] **B. Prompting de Síntese Hierárquica:** Instruir a LLM com mais rigor: *"O contexto interno é a FONTE DE VERDADE. A Web só preenche lacunas. Em caso de mistura de contextos distintos, mantenha-os separados"*.
- [ ] **C. Arquitetura Multi-Step (Drafting):** Separar a formulação de resposta. O agente gera um rascunho com o RAG; e depois só busca na web o que faltou, unificando no final.
- [ ] **D. Reranking Pós-Recuperação:** Adicionar um modelo de Reranker (ex: `cohere-rerank-3.5`) após o Pinecone, garantindo que a LLM receba apenas o "filé mignon" da informação vetorial, reduzindo ruído.

**Próximo Passo:** Construir um script de Benchmark (`eval_merge.py`) com perguntas complexas para medir o grau de alucinação e avaliar as hipóteses acima.

---

## 2. Busca e Precisão de Entidades
- [ ] **Hybrid Search no Pinecone:** Misturar busca semântica (vetorial) com busca léxica (palavras-chave via BM25) para aumentar a precisão de buscas por nomes exatos de deputados, políticos ou siglas muito específicas que os LLMs e Embeddings atuais confundem.

## 3. Arquitetura de Dados Estruturada
- [ ] **Banco de Dados Relacional (PostgreSQL):** Adicionar um banco SQL para salvar o perfil e o histórico determinístico de cada deputado. Isso permite respostas analíticas e exatas (ex: "Quantas vezes o deputado X votou Sim neste ano? Onde ele gastou mais CEAPS?") sem depender da capacidade analítica da LLM, que historicamente falha com matemática e consolidações.

## 4. Recursos de Usuário e Segurança
- [ ] **Autenticação:** Implementar um sistema de login para que os usuários possam persistir seus históricos de chat, salvar respostas favoritas e, futuramente, criar alertas automatizados sobre novos projetos de lei ou gastos.
