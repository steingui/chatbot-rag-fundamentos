# 🚀 Roadmap de Melhorias Frontend - RAG Político

Este documento estabelece o plano estratégico de evolução da interface do usuário (Vite + React + TypeScript), focado em **Segurança**, **Performance/Otimização**, **Escalabilidade** e **Manutenibilidade/DX**.

---

## 1. 🛡️ Segurança (Security & Compliance)

| Item | Descrição & Ação Técnica | Prioridade | Status |
| :--- | :--- | :---: | :---: |
| **Sanitização XSS** | Integrar `DOMPurify` (ou `isomorphic-dompurify`) no retorno da função `formatMarkdown()` para higienizar qualquer HTML renderizado via `dangerouslySetInnerHTML` contra injeção de scripts maliciosos oriundos da busca web. | `Alta` | ✅ Concluído |
| **Proteção Anti-Spam** | Implementar *debounce* e desabilitação estrita no frontend durante o trânsito da requisição para evitar chamadas duplicadas simultâneas. | `Média` | ✅ Concluído |
| **Políticas de Links** | Garantir que todas as fontes externas utilizem `rel="noopener noreferrer"` e passem por um validador de protocolo (`http:`, `https:`) prevenindo ataques de `javascript:`. | `Média` | ✅ Concluído |

---

## 2. ⚡ Otimizações & Performance

| Item | Descrição & Ação Técnica | Prioridade | Status |
| :--- | :--- | :---: | :---: |
| **Virtualização de Lista** | Adicionar `tanstack-virtual` ou `react-window` na renderização das mensagens para manter 60 FPS mesmo em sessões com centenas de respostas. | `Alta` | ✅ Concluído |
| **Streaming via SSE** | Migrar a comunicação `/chat` de requisição HTTP estática para Server-Sent Events (SSE), permitindo o efeito *typewriter* (token por token) e reduzindo a sensação de latência. | `Alta` | ✅ Concluído |
| **Cache Inteligente de Sugestões** | Implementar `TanStack Query` (React Query) ou `SWR` para gerenciar chamadas de `/suggestions` com cache e revalidação em segundo plano sem re-renders desnecessários. | `Média` | ✅ Concluído |
| **Chunk Splitting & Asset Purge** | Configurar `manualChunks` no `vite.config.ts` para separar bibliotecas pesadas (`lucide-react`, `marked`) da aplicação principal, reduzindo o *First Contentful Paint (FCP)*. | `Média` | ✅ Concluído |

---

## 3. 🏗️ Escalabilidade & Arquitetura de Código

| Item | Descrição & Ação Técnica | Prioridade | Status |
| :--- | :--- | :---: | :---: |
| **Componentização Modular** | Decompor o arquivo monolítico `App.tsx` em componentes menores e de responsabilidade única: `SessionSidebar`, `ChatHeader`, `MessageList`, `MessageItem`, `SuggestionGrid`, `ModelSelector`. | `Alta` | ✅ Concluído |
| **Gerenciamento de Estado** | Adotar `Zustand` ou `React Context API` para isolar o estado de sessões, modelo selecionado e loading do fluxo de renderização dos componentes. | `Alta` | ✅ Concluído |
| **Persistência Local (Offline-First)** | Armazenar o histórico de mensagens e ID de sessões no `localStorage` ou `IndexedDB`, permitindo que o usuário recarregue a página sem perder o contexto ativo. | `Média` | ✅ Concluído |

---

## 4. 🧪 Manutenibilidade & Experiência de Desenvolvimento (DX)

| Item | Descrição & Ação Técnica | Prioridade | Status |
| :--- | :--- | :---: | :---: |
| **Suíte de Testes Unitários** | Configurar `Vitest` + `React Testing Library` para validar a renderização de markdown, seleção de modelos e gerenciamento de abas/sessões. | `Alta` | ✅ Concluído |
| **Testes E2E (Playwright)** | Adicionar pipeline de testes automatizados E2E cobrindo fluxo completo: digitação, resposta do bot, seleção de modelos e clique nas badges de sugestão. | `Média` | ⏳ Pendente |
| **Design System Tokens** | Extrair variáveis globais de CSS (`index.css`) em um arquivo de tokens reutilizável (`theme.ts` / CSS Modules) garantindo suporte facilitado a Dark/Light modes. | `Baixa` | ⏳ Pendente |
