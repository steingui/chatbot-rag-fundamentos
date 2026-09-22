# 💰 Backlog 06: Monetização Web (AdSense/GPT Ads + Paywall Stripe) & Publicação

> **Objetivo:** Monetizar o webapp (React + Vite no Firebase Hosting) com anúncios web — Google AdSense / Google Ad Manager (GPT) — a cada 3 prompts e assinatura Freemium/Pro via Stripe. Sem submissão a lojas mobile.

---

## 🎯 QUICK-WIN — Anúncios Web Reais e Paywall Stripe

> **Foco imediato:** sair do mock atual e colocar anúncio web real com verificação server-side + cobrança recorrente.
> A UI já existe ([`RewardedAdModal.tsx`](../../frontend/src/components/RewardedAdModal.tsx)) e o contador de prompts já existe ([`useChatStore.ts`](../../frontend/src/store/useChatStore.ts)).
> O que falta é **rede de anúncios web + SDK real (GPT) + verificação server-side + consentimento + paywall Stripe**.

### Fase 1 — Configurar a rede de anúncios web (pré-requisito de tudo)
- [ ] **[QW-101]** Criar conta no Google AdSense, cadastrar o site (`politichat.com.br`) e aguardar aprovação.
- [ ] **[QW-102]** Criar conta no Google Ad Manager (GPT) e gerar as ad units do frontend web (display/vignette/rewarded).
- [ ] **[QW-103]** Cadastrar dados bancários + formulário fiscal W-8BEN (Brasil) no AdSense para habilitar pagamento (threshold: **US$ 100**).

### Fase 2 — SDK real substituindo o mock
- [ ] **[QW-201]** Carregar `gpt.js` no [`index.html`](../../frontend/index.html) e implementar o bridge real `__adsBridge.showRewarded` resolvendo `true` **apenas** no evento de recompensa (`SlotOnSessionEnd`), substituindo o mock de [`rewardedAds.ts`](../../frontend/src/lib/rewardedAds.ts).
- [ ] **[QW-202]** Implementar slots display (banner/vignette) e Auto Ads nas páginas do webapp, sem quebrar o layout do chat.
- [ ] **[QW-203]** Config de produção: `VITE_ADS_MODE=gpt` + ad unit IDs em variáveis de ambiente no Firebase Hosting.

### Fase 3 — Verificação server-side (MON-606) — protege a receita contra bypass
- [ ] **[QW-301]** Criar endpoint FastAPI em [`backend/api/`](../../backend/api/) para validar a recompensa (Ad Manager/GPT SSV ou token assinado): recebe `ssv_signature` + `custom_data`, valida assinatura com `AD_WEB_SSV_*` e libera saldo/token de prompts.
- [ ] **[QW-302]** Injetar `custom_data` assinado (ex.: `guest_id`) no ad request e substituir o `unlockRewardedAd()` client-side ([`useChatStore.ts`](../../frontend/src/store/useChatStore.ts:227)) pelo unlock via backend.
- [ ] **[QW-303]** Adicionar `AD_WEB_SSV_*` ao [`.env.example`](../../.env.example).

### Fase 4 — Consentimento (obrigatório p/ ads)
- [ ] **[QW-401]** Integrar Google CMP (Privacy & Messaging / Funding Choices) para LGPD/GDPR antes de exibir anúncios.

---

## 🔀 Ordem de Execução do Quick-Win

### Pré-requisito manual (sem código)
1. **[QW-101]** Criar conta Google AdSense, cadastrar `politichat.com.br` e aguardar aprovação.
2. **[QW-102]** Criar conta Google Ad Manager (GPT) e gerar as ad units do frontend (display/vignette/rewarded).
3. **[QW-103]** Cadastrar dados bancários + W-8BEN no AdSense (threshold US$ 100).

### Código (frontend)
4. **[QW-201]** Carregar `gpt.js` no [`index.html`](../../frontend/index.html) e implementar o bridge `__adsBridge.showRewarded` resolvendo `true` só em `SlotOnSessionEnd`, substituindo o mock de [`rewardedAds.ts`](../../frontend/src/lib/rewardedAds.ts).
5. **[QW-202]** Slots display (banner/vignette) + Auto Ads no webapp, sem quebrar o layout do chat.
6. **[QW-203]** `VITE_ADS_MODE=gpt` + ad unit IDs via env no Firebase Hosting.

### Código (backend + env)
7. **[QW-301]** Endpoint FastAPI para validar SSV (recebe `ssv_signature` + `custom_data`, valida com `AD_WEB_SSV_*` e libera saldo).
8. **[QW-302]** Injetar `custom_data` assinado (`guest_id`) e trocar o `unlockRewardedAd()` client-side em [`useChatStore.ts`](../../frontend/src/store/useChatStore.ts:227) pelo unlock via backend.
9. **[QW-303]** Adicionar `AD_WEB_SSV_*` ao [`.env.example`](../../.env.example).

### Consentimento
10. **[QW-401]** Google CMP (Privacy & Messaging) para LGPD/GDPR antes de exibir anúncios.

> **Ordem de implementação de código:** QW-201 → QW-202 → QW-203 → QW-301 → QW-302 → QW-303 → QW-401.
> As tasks QW-101..103 podem ser executadas em paralelo com o desenvolvimento.

---

## 📋 Tarefas & Histórias de Usuário (escopo completo)

### 6.1 Anúncios Web (AdSense/GPT — 1 Ad / 3 Prompts)
- [ ] **[MON-601]** Integrar GPT Ads (`gpt.js`) no frontend web: slots display (banner/vignette) + rewarded via bridge `__adsBridge`.
- [x] **[MON-602]** Criar contador de tokens/prompts no `useChatStore`: a cada 3 prompts consumidos, exige visualização de 1 anúncio para desbloquear o próximo lote.
- [x] **[MON-603]** Implementar tela modal de "Assistir Vídeo para Continuar" com contador transparente e fallback caso o anúncio falhe ao carregar (Fill Rate limit).
- [ ] **[MON-604]** Otimização de eCPM/layout web: posicionamento de slots acima da dobra, lazy load e viewability para eCPM saudável em tráfego brasileiro.
- [x] **[MON-605]** Ad Fill Rate & Fallback Engine: Garantir fallback gracioso (Rewarded → Display/Vignette → Free Grace) caso não haja anúncio disponível na região.
- [ ] **[MON-606]** Proteção Anti-Bypass Backend: Validar tokens de conclusão de ad (Ad Server Verification callbacks) no backend FastAPI antes de liberar o saldo de prompts.
- [ ] **[MON-607]** Reativar o banner de antecipação de lote ("1 prompt restante no lote gratuito") em [`RewardedAdModal.tsx`](../../frontend/src/components/RewardedAdModal.tsx) — removido temporariamente até a rede de anúncios real (QW-201) estar ativa; a trava `adLocked` e o modal de desbloqueio permanecem funcionais.

### 6.2 Paywall Freemium/Pro (Stripe)
- [ ] **[PAY-601]** Criar produtos e preços no Stripe (plano **Pro** mensal e anual).
- [ ] **[PAY-602]** Backend FastAPI: endpoint `create-checkout-session` + webhook `stripe` (verificar assinatura) para ativar/desativar o plano Pro.
- [ ] **[PAY-603]** Frontend: página de pricing + botão "Assinar Pro" redirecionando ao Stripe Checkout.
- [ ] **[PAY-604]** Limites por tier no backend: **Free** = 3 prompts/lote com anúncio; **Pro** = ilimitado e sem anúncios.
- [ ] **[PAY-605]** Portal de assinatura (Stripe Customer Portal) para upgrade/cancelamento sem sair do app.

### 6.3 Publicação & Analytics
- [ ] **[PUB-601]** Deploy do webapp no Firebase Hosting com ads + paywall ativos.
- [ ] **[PUB-602]** Analytics de receita: eventos de conversão (anúncio concluído, assinatura iniciada/concluída) via Google Analytics/GA4.
- [ ] **[PUB-603]** Publicar páginas de Privacidade/Termos (LGPD) e política de consentimento de anúncios.
