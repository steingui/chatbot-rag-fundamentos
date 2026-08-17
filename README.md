# 🏛️ Chatbot RAG - Câmara dos Deputados

Este projeto utiliza inteligência artificial para responder perguntas sobre o histórico de votações da Câmara dos Deputados Brasileiros, baseando-se em dados reais.

## 🚀 Como Testar a API em Produção

O backend está ativo no Render e atualizado automaticamente com as últimas votações.

Você pode enviar perguntas para a IA através do terminal usando `curl`:

```bash
curl -X POST "https://chatbot-rag-api-q2k5.onrender.com/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "Sua pergunta aqui"}'
```

## 💬 Sugestões de Prompts

Aqui estão algumas ideias do que você pode perguntar para a IA:

1. **Visão Geral:**
   > `"Quais foram as últimas votações registradas na Câmara?"`
2. **Posicionamento Específico:**
   > `"Como o deputado Alberto Fraga (PL-DF) votou na última sessão?"`
3. **Resumo por Partido:**
   > `"Qual foi o padrão de votos do partido PT nas votações mais recentes?"`
4. **Análise de Abstenções:**
   > `"Quais deputados se abstiveram de votar nas proposições analisadas?"`

---
*Para ver como a arquitetura funciona por trás dos panos, confira `docs_projeto/how-this-works.md`.*
