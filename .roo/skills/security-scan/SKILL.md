---
name: security-scan
description: Varre a codebase, histórico git, dependências (SCA), IaC/Docker, CI/CD, configs e lógica RAG em busca de falhas, priorizando os achados com gate Jev e gerando um relatório priorizado em Markdown.
---

# Auditoria Global de Segurança e Gaps (Completa)

## Instructions

1. **SAST (Código-Fonte):** Analise o código em busca de vulnerabilidades (OWASP Top 10, injeções, falhas de validação de input).
2. **SCA (Dependências):** Inspecione `requirements.txt`, `poetry.lock` e `package.json` por pacotes desatualizados ou com CVEs conhecidas.
3. **IaC & Contentores:** Verifique `Dockerfile` e `docker-compose.yml` quanto a privilégios de root, exposição excessiva e secrets em build.
4. **CI/CD & Automação:** Audite ficheiros em `.github/workflows/` contra comandos inseguros e ausência de pinagem de actions.
5. **Configurações & Histórico (Git):** Revise ficheiros de ambiente, templates e `git log -p` para detetar chaves de API ou tokens expostos.
6. **Lógica de RAG & Endpoints:** Valide potenciais pontos de injeção de prompt, ausência de rate limiting ou validação estricta de schemas.
7. **Priorização com Jev (MCP `jevcore`):** Após coletar os achados, chame `jev_rank` com `query` descrevendo o critério `"Quão crítica é esta falha para segurança e integridade do produto?"` e `candidates` contendo cada achado (título + local + impacto resumido). Use o ranking para agrupar por severidade (**Crítico**, **Alto**, **Médio**, **Baixo**).
   - **Fallback:** Jev indisponível (`None`, erro ou timeout) ⇒ classificar manualmente por impacto/explorabilidade, como hoje. O Jev otimiza, nunca bloqueia a varredura.
   - **Budget:** limite `jev_rank` ao top-N de achados (ex.: máx. 20 candidatos por chamada); achados além disso seguem a classificação manual.
8. **Relatório Priorizado:** Gere o relatório em Markdown com o impacto e plano de mitigação, na ordem de severidade definida no passo 7.

## Notas de integração

- Modelo fixo `typesafe/jev-1.13` via `OPENROUTER_API_KEY` (nunca hardcode).
- Secrets detetados **nunca** são enviados ao Jev nem a qualquer serviço externo; apenas o título/local do achado (sem o valor da secret).
