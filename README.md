# 🏛️ Chatbot RAG Político-Eleitoral

Este projeto utiliza inteligência artificial avançada (RAG - *Retrieval-Augmented Generation*) para responder perguntas sobre o cenário político brasileiro. A IA cruza dados de múltiplas fontes oficiais para gerar respostas precisas e livres de alucinações.

## 🏗️ Arquitetura e Fontes de Dados (Fase 4)

O sistema ingere e processa dados automaticamente usando **GitHub Actions** em 6 pipelines integradas:
1. **Votações e Proposições da Câmara (Diário/Semanal)**
2. **Dados do TSE - DivulgaCandContas (Semanal)**
3. **Planos de Governo e Fact-Checking (Diário/Mensal)**
4. **Querido Diário - Atos Municipais (Diário)**
5. **Transparência e Execução Orçamentária CGU (Semanal)**
6. **Autonomous QA Multi-Agent Pipeline (Diário com Auto-Cura)**

A Inteligência Artificial é impulsionada por arquitetura **Multi-Provider (Google Gemini 3.7 Flash, Gemini 3.6 Flash, Llama 3.3, DeepSeek R1)**, e as buscas rodam no **Pinecone Vector Database** via Busca Híbrida (Dense Embeddings + BM25 Sparse).

## 🚀 Como Testar a API em Produção

O backend (FastAPI) está hospedado no Google Cloud Run, e o frontend no Firebase Hosting. Teste a API via `curl`:

```bash
curl -X POST "https://chatbot-rag-api-1043919586992.southamerica-east1.run.app/api/v1/chat" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <id_token_firebase>" \
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
*Status do Projeto: Fase 4 Concluída (Busca Híbrida Dense+BM25 + QA Autônomo Multi-Agente + Firestore Auth + GCP Cloud Run API + Firebase Hosting).*

