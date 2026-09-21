---
name: web-performance-auditor
description: Audita uma URL de performance e SEO executando o fluxo completo do usuário com Playwright, analisando achados com docs do Context7 e criando uma issue detalhada no GitHub com evidências e correções propostas.
---

# Web Performance & SEO Auditor

## When to use
Use esta skill quando o usuário pedir para:
- "auditar a performance de [URL]"
- "verificar o SEO da minha página"
- "analisar o fluxo do usuário de [URL]"
- ou digitar /audit-url

## Prerequisites
- O MCP playwright deve estar configurado.
- O MCP context7 deve estar configurado.
- O MCP github deve estar configurado com um token válido com escopo repo.
- O usuário deve fornecer: uma URL alvo e, opcionalmente, um repositório GitHub no formato owner/repo.

## Procedure

### 1. Reconnaissance
- Pergunte ao usuário a URL alvo e o repositório GitHub (owner/repo) se não fornecidos.
- Pergunte ao usuário para descrever o fluxo principal a ser exercitado (ex: "entrar na home -> buscar -> abrir produto -> adicionar ao carrinho"). Se não fornecido, use o padrão: carregar página -> rolar até o fim -> clicar no CTA principal -> preencher e submeter o formulário principal -> navegar para uma página secundária.

### 2. Capture page data (Playwright MCP)
- Navegue até a URL alvo em um contexto de navegador novo.
- Ative a interceptação de requests/responses.
- Execute o fluxo do usuário passo a passo, capturando em cada etapa:
  - Um screenshot full-page.
  - Um screenshot da viewport.
  - A árvore DOM (page.content() ou equivalente).
  - Erros e warnings do console.
  - Requests de rede falhos (4xx, 5xx).
- Colete métricas de performance via performance.getEntries() e Navigation Timing API:
  - domContentLoaded, loadEventEnd, firstContentfulPaint, largestContentfulPaint.
  - Tamanho total de transferência e número de requests.
  - Maiores recursos individuais (imagens, JS, CSS).
- Extraia metadados de SEO:
  - title, meta description, link canônico, tags Open Graph, Twitter cards.
  - Presença de robots.txt e sitemap.xml.
  - Hierarquia de headings (h1-h6).
  - Atributos alt e width/height de imagens.

### 3. Analyze with Context7
- Detecte o framework e a versão do repositório (ex: leia package.json via GitHub MCP, ou infera do DOM).
- Use o MCP context7 para buscar as docs mais recentes daquele framework sobre:
  - Otimização de Core Web Vitals
  - Otimização de imagens
  - Boas práticas de metadados / SEO
- Cruze as métricas capturadas contra as recomendações oficiais.
- Produza uma lista priorizada de achados. Classifique a severidade:
  - Critical: quebra funcionalidade ou bloqueia renderização.
  - High: degrada significativamente LCP/CLS/INP ou ranking de SEO.
  - Medium: subótimo mas funcional.
  - Low: polimento opcional.

### 4. Diagnose
Para cada achado, identifique:
- O sintoma (valor medido vs. limite recomendado).
- A causa raiz provável.
- Os arquivos no repositório responsáveis (busque via GitHub MCP usando search_code).

Achados comuns para procurar:
- LCP > 2.5s, CLS > 0.1, INP > 200ms.
- Imagens sem width/height, sem loading=lazy, ou em formatos legados (PNG/JPEG em vez de WebP/AVIF).
- meta description ausente ou duplicada, canonical ausente, tags OG ausentes.
- CSS/JS bloqueando renderização no head.
- sitemap.xml / robots.txt ausentes ou malformados.
- Erros de console ou 404s em requests de rede.

### 5. Create a GitHub Issue (GitHub MCP)
- Use o MCP github para chamar create_issue no repositório alvo.
- **Título (formato canônico, sempre):** `[Perf/SEO Audit] <domain> - N findings (X critical, Y high, Z medium, W low)`
  - `<domain>` é o domínio **sem** `https://` (ex: `rag-eleicoes.web.app`).
  - `N` = total de findings = X + Y + Z + W. Listar **todas** as severidades, mesmo as zeradas.
- **Corpo da issue em markdown**, com as seções EXATAS nesta ordem. Não adicionar seções extras como "Arquivos afetados" ou "Anexos"; screenshots/arquivos entram em `**Evidência:**` ou `**Causa raiz:**`:
  1. `## Audit Summary` — tabela `| Campo | Valor |` com: `URL`, `Data`, `Framework`, `Fluxo exercitado`, `Resultado do fluxo`.
  2. `## Core Web Vitals` — tabela `| Métrica | Medido | Alvo | Status |` (TTFB, FCP, LCP, CLS, INP, transferência), seguida de nota `>` opcional.
  3. `## Findings` — um heading por achado no formato `### N. <emoji> <SEVERIDADE> — Título`, onde:
     - `🔴 CRITICAL` · `🔴 HIGH` · `🟡 MEDIUM` · `🟢 LOW`.
     - Cada finding usa labels em negrito nesta ordem: `**O quê:**`, `**Por que importa:**`, `**Causa raiz:**` (quando aplicável), `**Como corrigir:**`, `**Evidência:**`.
     - Separar findings com `---`.
  4. `## Próximos passos recomendados` — lista numerada, referenciando o número de cada finding.

### 6. Report back to the user
- Imprima a URL da issue do GitHub.
- Resuma os 3 principais achados e o impacto estimado.

## Output
Uma única issue no GitHub contendo todas as evidências, diagnóstico e correções propostas, pronta para o time triar.
