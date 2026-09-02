# 📺 Backlog 06: Monetização por Rewarded Ads (AdMob/AppLovin) & Submissão às Lojas

> **Objetivo:** Implementar modelo de monetização baseado em anúncios premiados (Rewarded Video Ads) a cada 3 prompts e realizar submissão na Apple App Store e Google Play Store.

---

## 🎯 Tarefas & Histórias de Usuário

### 6.1 Anúncios Premiados (Rewarded Ads — 1 Ad / 3 Prompts)
- [ ] **[MON-601]** Integrar SDK Google Mobile Ads / AdMob (`react-native-google-mobile-ads`) ou AppLovin MAX no app mobile.
- [ ] **[MON-602]** Criar contador de tokens/prompts no `useChatStore`: a cada 3 prompts consumidos, exige visualização de 1 Rewarded Video Ad para desbloquear o próximo lote.
- [ ] **[MON-603]** Implementar tela modal de "Assistir Vídeo para Continuar" com contador transparente e fallback caso o anúncio falhe ao carregar (Fill Rate limit).
- [ ] **[MON-604]** Mediação de eCPM (AdMob + AppLovin MAX + Unity Ads): Configurar leilão em tempo real (in-app bidding) para garantir eCPM > $2.50 em tráfego brasileiro.
- [ ] **[MON-605]** Ad Fill Rate & Fallback Engine: Garantir fallback gracioso (Rewarded Video → Interstitial Banner → Free Grace) caso não haja anúncio disponível na região.
- [ ] **[MON-606]** Proteção Anti-Bypass Backend: Validar tokens de conclusão de ad (Ad Server Verification callbacks) no backend FastAPI antes de liberar o saldo de prompts.

### 6.2 Submissão & Publicação
- [ ] **[STORE-605]** Configurar conta de desenvolvedor no Apple Developer Program ($99/ano) e preencher formulários de privacidade sobre anúncios (ATT - App Tracking Transparency).
- [ ] **[STORE-606]** Configurar conta de desenvolvedor no Google Play Console ($25 único) e declarar uso de IDs de Anúncio (Ad ID).
- [ ] **[STORE-607]** Gerar screenshots promocionais e ícone oficial (1024x1024) para todas as resoluções de tela.
- [ ] **[STORE-608]** Submeter builds (AAB para Google Play e IPA para TestFlight/App Store) e acompanhar processo de App Review.
