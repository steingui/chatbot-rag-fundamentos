# 🏛️ Chatbot RAG Político-Eleitoral

Este projeto utiliza inteligência artificial avançada (RAG - *Retrieval-Augmented Generation*) para responder perguntas sobre o cenário político brasileiro. A IA cruza dados de múltiplas fontes oficiais para gerar respostas precisas e livres de alucinações.

## 🏗️ Arquitetura e Fontes de Dados (Fase 2)

O sistema ingere e processa dados automaticamente usando **GitHub Actions** em três pipelines distintas:
1. **Votações da Câmara (Diário):** Coleta como deputados votaram, cruzando as siglas das leis com a *Ementa Oficial*.
2. **Dados do TSE (Semanal):** Processa dados de financiamento de campanha e evolução patrimonial de candidatos.
3. **Planos de Governo e Fact-Checking (Mensal):** Extrai PDFs (propostas) e cruza discursos com portais confiáveis (ex: G1 Fato ou Fake).

A Inteligência Artificial é impulsionada pelo **Google Gemma 4 (31B)** via OpenRouter, e as buscas semânticas rodam no **Pinecone Vector Database**.

## 🚀 Como Testar a API em Produção

O backend (FastAPI) está hospedado no Render, com a base vetorial sempre atualizada. Teste via `curl`:

```bash
curl -X POST "https://chatbot-rag-api-q2k5.onrender.com/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "Resuma a PEC 45/2019 e diga se é verdade que ela aumenta imposto sobre cestas básicas."}'
```

## 💬 Sugestões de Prompts

1. **Votações e Ementas:**
   > `"Qual foi o padrão de votos do partido PT nas votações mais recentes?"`
2. **Fact-Checking (Fato ou Fake):**
   > `"É verdade que a PEC 45/2019 vai tributar livros?"`
3. **Dados de Campanha (TSE):**
   > `"Quais foram os maiores doadores da campanha de João Fictício e qual seu patrimônio?"`
4. **Planos de Governo:**
   > `"Quais as propostas da candidata Maria Exemplo para o Meio Ambiente?"`

---
*Status do Projeto: Fase 2 (RAG e Dados) Concluída. Próximo passo: Desenvolvimento do Frontend.*
