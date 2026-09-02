# 📱 Backlog 03: App Mobile React Native (Expo)

> **Objetivo:** Desenvolver o aplicativo mobile cross-platform (iOS/Android) com UX premium, suporte offline, streaming e feedback háptico.

---

## 🎯 Tarefas & Histórias de Usuário

### 3.1 Setup & Arquitetura Base
- [ ] **[MOB-301]** Inicializar app React Native com Expo SDK 52 e `expo-router` no diretório `/mobile`.
- [ ] **[MOB-302]** Configurar sistema de rotas baseadas em arquivo (`/app/index.tsx`, `/app/chat/[id].tsx`, `/app/profile.tsx`).
- [ ] **[MOB-303]** Reutilizar e adaptar stores Zustand do frontend web (`useChatStore`, `useAuthStore`).
- [ ] **[MOB-304]** Configurar UI Design System (Tamagui ou React Native Paper) alinhado com a paleta dark/light mode do projeto.

### 3.2 Experiência do Usuário (UX) & Recursos Nativos
- [ ] **[MOB-305]** Implementar visualização Chat-First com Bottom Sheet expansível para alternância de sessões.
- [ ] **[MOB-306]** Criar bar de ações rápidas (chips deslizáveis acima do teclado) para sugestões dinâmicas de perguntas.
- [ ] **[MOB-307]** Integrar Haptic Feedback (`expo-haptics`) ao enviar mensagens, receber dados e alternar opções.
- [ ] **[MOB-308]** Renderizar mensagens em formato Markdown com suporte a citação inline de fontes (`react-native-markdown-display`).
- [ ] **[MOB-309]** Implementar suporte a cache offline local com `expo-sqlite` para leitura de histórico sem conexão.
- [ ] **[MOB-310]** Configurar Deep Links (`politichat://chat?q=...`) para compartilhamento direto de buscas.
- [ ] **[MOB-311]** UX de Recompensa de Ads: Modal fluido de "+3 perguntas liberadas" ao assistir anúncio, sem quebrar o fluxo conversacional.
- [ ] **[MOB-312]** UX de Graceful Degradation: Desbloquear acesso automaticamente se o anúncio falhar em carregar (Ad Failure/Fill rate), evitando frustração ou travamento da interface.
