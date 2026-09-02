# 🔒 Backlog 05: Autenticação, Autorização & Segurança LGPD

> **Objetivo:** Proteger a API contra abusos, gerenciar identidades de usuários nativamente e garantir conformidade com LGPD e diretrizes de lojas.

---

## 🎯 Tarefas & Histórias de Usuário

### 5.1 Autenticação & Validação
- [ ] **[SEC-501]** Configurar projeto no Firebase Auth habilitando provedores sociais (Google Sign-In e Apple Sign-In).
- [ ] **[SEC-502]** Criar middleware FastAPI de validação de `id_token` do Firebase, injetando `user_id` e privilégios no contexto das requisições.
- [ ] **[SEC-503]** Substituir `OriginCheckMiddleware` por validação de Bearer Token nas rotas protegidas da API.
- [ ] **[SEC-507]** Autenticação Anônima (`signInAnonymously()`): Liberar degustação imediata sem formulário no primeiro acesso do app/web.
- [ ] **[SEC-508]** Vinculação de Conta (`linkWithCredential()`): Converter a conta anônima em conta social (Google/Apple) mantendo o histórico de chats intacto.
- [ ] **[SEC-509]** Barreira de Autenticação Progressiva: Exibir bloqueio elegante requerendo cadastro após 3 a 5 prompts de teste.

### 5.2 Segurança & Conformidade (LGPD / App Store / Play Store)
- [ ] **[SEC-504]** Desenvolver página de Política de Privacidade e Termos de Uso (`politichat.com.br/privacidade`).
- [ ] **[SEC-505]** Criar rotinas e endpoints para exclusão completa de conta de usuário e dados pessoais (Requisito obrigatório Apple/LGPD).
- [ ] **[SEC-506]** Auditar retornos de erro da API para garantir zero exposição de dados sensíveis ou stack traces em produção.
