# Persona: Cientista Político / Pesquisador Acadêmico

- **Nome**: Dr. Arnaldo Rocha
- **Perfil**: Professor e pesquisador universitário que estuda comportamento parlamentar, disciplina partidária e transição de votos em pautas setoriais.
- **Conhecimento Técnico**: Alto.
- **Estilo de Comunicação**: Acadêmico, rigoroso, focado em agregação de dados e séries históricas.

---

## Objetivos no Produto
1. Realizar consultas analíticas de alta complexidade envolvendo múltiplos parlamentares e temas.
2. Obter mapeamentos completos de mudanças de voto sem corte de resposta ou truncamentos (`...`).
3. Avaliar a coerência do alinhamento partidário em votações de grande relevância nacional.

---

## Cenários de Teste & Critérios de Bug
- **Bug de Truncamento**: Respostas contendo reticências (`...`) ou listas incompletas de parlamentares.
- **Bug de Limite de Tokens**: Falha na geração por estouro de contexto ao solicitar rankings extensos.
- **Bug de Recuperação Híbrida**: RAG omitindo dados históricos mantidos no índice Pinecone/BM25.

---

## Template de Prompt Tipico
> "Liste os parlamentares que mais mudaram de voto em pautas ambientais nos últimos 4 anos. A resposta deve ser completa e não conter reticências (...)."
