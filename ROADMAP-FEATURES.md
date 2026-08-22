# ROADMAP: Melhorias de Produto e Arquitetura

Este documento detalha o planejamento para duas features estratégicas voltadas para o engajamento do usuário (UX) e a coerência das respostas da Inteligência Artificial (AI Core).

---

## 1. Revitalização das Sugestões de Prompts (Zero-Count & Curious Prompts)

**Objetivo:** Substituir a mecânica atual baseada em estatísticas de uso (com contadores visíveis) por uma curadoria de perguntas altamente instigantes, provocativas e perfeitamente alinhadas com as nossas bases de dados oficiais (TSE, Portal da Transparência, Câmara e Senado).

### Problema Atual
As sugestões mostram números (ex: "Quantas vezes a pergunta X foi feita") e tendem a ser perguntas genéricas e repetitivas geradas pelos próprios usuários, reduzindo o potencial de exploração da plataforma.

### Passos de Implementação (Actionables):
- [ ] **Fase 1: Curadoria Hardcoded de "Iscas" (Ganhos Rápidos)**
  - Remover a lógica de contadores do frontend e do backend.
  - Substituir o feed do SQLite por uma lista randômica de perguntas elaboradas manualmente para causar curiosidade. Exemplos:
    - *"Qual é a correlação entre as empresas que mais doaram no TSE e os maiores contratos no Portal da Transparência?"*
    - *"Liste os parlamentares que mais mudaram de voto em pautas ambientais nos últimos 4 anos."*
    - *"Quais são as emendas parlamentares mais atípicas pagas no último mês?"*
- [ ] **Fase 2: Geração Dinâmica (Cronjob LLM)**
  - Criar um script rodando via GitHub Actions que, semanalmente, lê os *chunks* mais recentes injetados no Pinecone (ex: um novo projeto de lei polêmico) e gera dinamicamente 3 perguntas curiosas e provocativas sobre aquele assunto atual.

---

## 2. Discovery: Otimização da Estratégia de Merge (ReAct Agent + Vector DB)

**Objetivo:** Melhorar a coesão, precisão e ausência de conflitos quando a LLM precisa misturar o contexto oficial imutável (Pinecone) com informações dinâmicas da web (DuckDuckGo Search).

### Problema Atual
Atualmente, o Agente ReAct pode se confundir ao tentar amalgamar documentos legais extensos com resultados de notícias rápidas da web, gerando respostas não lineares, priorizando a web em detrimento do dado oficial, ou perdendo o tracking exato da fonte.

### Hipóteses para Validação (Discovery):

- [ ] **A. Roteamento Semântico (Semantic Router) vs. Merge Fixo**
  - *Teste:* Em vez de enviar o Vector DB e a Web Tool simultaneamente para o Agente, criar um classificador inicial (Roteador). Ele decide: a pergunta precisa de dados históricos (apenas RAG), notícias de hoje (apenas Web), ou cruzamento de ambos? Isso economiza tokens e reduz alucinações por excesso de contexto ruidoso.
- [ ] **B. Prompting de Síntese Hierárquica**
  - *Teste:* Reescrever o System Prompt final instruindo explicitamente a hierarquia de confiança: *"O 'Contexto Interno' (Câmara/Senado/TSE/CGU) é a FONTE DE VERDADE ABSOLUTA. A 'Pesquisa Web' deve ser usada APENAS para preencher lacunas de atualidade. Em caso de divergência, informe a divergência e prevaleça o dado interno."*
- [ ] **C. Arquitetura Multi-Step (Drafting)**
  - *Teste:* Quebrar o merge em etapas. 
    1. Agente avalia o RAG e cria um rascunho de resposta (Draft 1).
    2. Agente consulta a Web para fatos que faltaram no Draft 1.
    3. Agente sintetiza tudo na Resposta Final.
    *(Trade-off: Aumenta a latência. Avaliar se o streaming consegue mascarar o tempo extra).*
- [ ] **D. Reranking Pós-Recuperação (Pinecone -> Cohere/BM25)**
  - *Teste:* O gargalo do Merge pode ser que o RAG está retornando muito "lixo" que confunde o Agente. Implementar um modelo de Reranker (ex: `cohere-rerank-3.5`) logo após a extração do Pinecone, garantindo que o Agente ReAct só receba as top-3 informações cirurgicamente perfeitas antes de acionar a ferramenta de Web Search.

### Próximo Passo do Discovery:
Construir um pequeno script de Benchmark (`eval_merge.py`). Criar 10 perguntas complexas e medir a precisão (accuracy) e coerência da resposta atual vs. aplicando a Hipótese B (Prompting Hierárquico) e a Hipótese A (Router).
