# Mapa de Componentes — RAG Político (Frontend)

## Árvore de Componentes

```
App.tsx (root)
├── SessionSidebar.tsx      # Sidebar esquerda fixa (240px)
├── ChatHeader.tsx           # Header do painel de chat
├── SuggestionGrid.tsx       # Grid de sugestões populares
├── MessageList.tsx          # Lista virtualizada de mensagens
│   └── SourceBadges.tsx     # Chips de fontes por mensagem
└── footer (inline)          # Input form + send button
    └── ModelSelector.tsx    # Dropdown embutido no header (não no footer)
```

## Detalhamento por Componente

### `App.tsx`
- **Responsabilidade**: Layout root (flexbox horizontal), input form, submit handler
- **Store deps**: `input`, `setInput`, `isLoading`, `fetchSuggestions`, `sendMessageStream`
- **Efeito**: `useEffect → fetchSuggestions()` no mount
- **Classe CSS root**: `.layout`

### `SessionSidebar.tsx`
- **Responsabilidade**: Gerenciar sessões de chat (criar, selecionar, fechar, limpar, resumir)
- **Store deps**: `sessions`, `activeIdx`, `setActiveIdx`, `addSession`, `closeSession`, `clearActiveSession`, `sendMessageStream`, `isLoading`
- **Ícones**: `Plus`, `Trash2`, `FileText` (lucide-react)
- **Comportamento**:
  - Botão `+` desabilitado quando `sessions.length >= 5` ou `isLoading`
  - "Resumir Conversa" envia prompt: `"Resuma nossa conversa em no máximo 1 tweet (280 caracteres)."`
  - "Resumir" desabilitado se não há mensagens do usuário na sessão ativa
  - Sessão ativa marcada com `▢`, inativas com `◯`
  - Botão `×` para fechar sessão (só visível no hover, só aparece se > 1 sessão)

### `ChatHeader.tsx`
- **Responsabilidade**: Exibir título do painel, sessão ativa, model selector, badge Pinecone
- **Store deps**: `sessions`, `activeIdx`
- **Subcomponente**: `<ModelSelector />`
- **Badge estático**: `PINECONE_INDEX: rag-fundamentos ONLINE`

### `ModelSelector.tsx`
- **Responsabilidade**: Dropdown para selecionar modelo LLM
- **Store deps**: `selectedModel`, `setSelectedModel`
- **Dados**: `FREE_MODELS[]` do store (5 modelos free-tier)
- **Classe CSS**: `.model-select`

### `SuggestionGrid.tsx`
- **Responsabilidade**: Grid horizontal de 4 sugestões populares com badge de contagem
- **Store deps**: `suggestions`, `sendMessageStream`, `isLoading`
- **Comportamento**: Click em sugestão → `sendMessageStream(sug.prompt)`
- **Classes CSS**: `.suggestions-container`, `.suggestion-card-item`, `.suggestion-card-count`

### `MessageList.tsx`
- **Responsabilidade**: Renderizar mensagens com virtualização (TanStack Virtual)
- **Store deps**: `sessions`, `activeIdx`, `isLoading`
- **Virtualização**: `useVirtualizer` com `estimateSize: 120px`, overscan: 5
- **Formatação**: `formatMarkdown()` (marked + DOMPurify) para mensagens bot
- **Subcomponente**: `<SourceBadges sources={msg.sources} />`
- **User header**: `you@rag:~$` (verde)
- **Bot header**: `⚡ ASSISTENTE (RAG)` (dourado)
- **Auto-scroll**: `scrollToIndex(lastIdx)` quando mensagens mudam

### `SourceBadges.tsx`
- **Responsabilidade**: Renderizar chips de fontes com validação de links
- **Props**: `sources: Source[]`
- **Segurança**: Apenas `http://` e `https://` são renderizados como links
- **Atributos de link**: `target="_blank" rel="noopener noreferrer"`
- **Sem URL válida**: chip renderizado como `<span>` (sem link)

## Zustand Store (`useChatStore.ts`)

### State

| Campo | Tipo | Default |
|-------|------|---------|
| `sessions` | `Session[]` | `[makeSession(0)]` ou localStorage |
| `activeIdx` | `number` | `0` |
| `input` | `string` | `''` |
| `selectedModel` | `string` | `FREE_MODELS[0].id` |
| `isLoading` | `boolean` | `false` |
| `suggestions` | `SuggestionItem[]` | 4 seeds hardcoded |

### Actions

| Action | Descrição |
|--------|-----------|
| `setInput(s)` | Atualiza campo de input |
| `setSelectedModel(m)` | Seleciona modelo LLM |
| `setActiveIdx(i)` | Muda sessão ativa |
| `addSession()` | Cria nova sessão (max 5) |
| `closeSession(i)` | Remove sessão por índice |
| `clearActiveSession()` | Reseta mensagens da sessão ativa |
| `setSuggestions(s)` | Atualiza sugestões |
| `fetchSuggestions()` | Busca sugestões (cache TTL → API fallback) |
| `sendMessageStream(q)` | Envia query via SSE streaming |

### Persistência

- Sessions: `localStorage['rag_chat_sessions_v1']` — salvo após cada mutação
- Suggestions: `localStorage['rag_suggestions_cache_v1']` — TTL 5min
- Rehidratação: `loadPersistedSessions()` no init do store
