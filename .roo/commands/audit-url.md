---
description: Audita uma URL para problemas de performance e SEO, exercitando o fluxo do usuário e criando uma issue no GitHub com evidências.
argument-hint: <URL> <owner/repo>
---

Use a skill `web-performance-auditor` para auditar a URL **$1** no repositório **$2**.

Siga a procedure da skill passo a passo:
1. Pergunte o fluxo do usuário se não estiver claro.
2. Capture dados com Playwright.
3. Analise com Context7.
4. Diagnostique os problemas.
5. Crie uma issue no GitHub com todas as evidências.
6. Reporte a URL da issue e os 3 principais achados.
