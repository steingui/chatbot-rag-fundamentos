# Skill: chatbot-rag-fundamentos

## Objetivo

Guiar o agente na operação segura e eficiente sobre o repositório
`chatbot-rag-fundamentos` — um chatbot político com RAG (Retrieval-Augmented
Generation), backend FastAPI, frontend React/Vite e pipelines de ingestão
automatizados.

## Instruções

1. **Leia `AGENTS.md`** na raiz do repositório. Ele é o contrato principal e
   contém estrutura, comandos, regras de segurança e convenções.

2. **Trate código, build, testes e configuração como fonte de verdade.**
   - Versões de dependências → `requirements.txt`, `frontend/package.json`
   - Runtime Python → `.python-version`
   - Deploy → `Dockerfile`, `render.yaml`
   - CI/CD → `.github/workflows/*.yml`
   - Nunca invente versões ou fatos não verificáveis nos artefatos.

3. **Carregue somente a orientação necessária para a tarefa.**
   - Os documentos em `.llm/` são detalhados e pesados.
   - Use a tabela em `AGENTS.md § 5` para decidir qual carregar.
   - Se a tarefa é simples (typo, README), não carregue nenhum.

4. **Valide documentação contra artefatos atuais.**
   - Antes de citar uma versão, confirme no arquivo de build real.
   - Se `.llm/` estiver desatualizado vs. código, atualize `.llm/` no mesmo commit.

5. **Priorize segurança** nos seguintes domínios:
   - **Endpoints**: Não expor rotas sem rate limiting ou autenticação.
   - **Dados**: Pinecone metadata sem PII. Inputs sanitizados via `guardrails.py`.
   - **Autenticação**: Secrets exclusivamente via env vars (`.env.example` como referência).
   - **Input**: Toda entrada do usuário passa por validação antes de processamento.
   - **Persistência**: Sem dados sensíveis em plain text.
   - **HTTP externo**: Timeout + retry obrigatórios em chamadas externas.
   - **Serialização**: Schemas tipados; nunca deserializar arbitrariamente.
   - **Secrets**: Nunca logar, expor ou hardcodar chaves/tokens.

## Referências

- `AGENTS.md` — contrato completo
- `.llm/` — documentação detalhada (sob demanda)
- `tests/` — testes existentes (rodar antes/depois de alterações)
