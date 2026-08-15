# Chatbot RAG (Fundamentos)

Projeto básico de Chatbot utilizando a técnica RAG (Retrieval-Augmented Generation).

## Arquitetura e Tecnologias
- **Vector DB**: ChromaDB (armazenamento local)
- **Framework**: LangChain
- **Embeddings**: HuggingFace (`all-MiniLM-L6-v2`)
- **LLM**: Integração via OpenRouter (ex: `meta-llama/llama-3-8b-instruct:free`)

## Como Executar

1. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure a API Key:
   Copie `.env.example` para `.env` e insira sua chave do OpenRouter:
   ```bash
   cp .env.example .env
   ```

3. Ingestão de Documentos:
   Adicione arquivos PDF ou Markdown na pasta `docs/` e execute:
   ```bash
   python ingest.py
   ```

4. Chat:
   Execute o script de chat para realizar perguntas sobre os documentos:
   ```bash
   python chat.py
   ```
