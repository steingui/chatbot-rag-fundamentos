# Design System v2 — RAG Político

## Identidade Visual

**Conceito**: Design System moderno inspirado no **Elera UI / shadcn/ui** — superfícies claras off-white, cards brancos elevados com sombras sutis, tipografia elegante e elementos em formato de pílula (*pill buttons*).

**Fonte primária**: `Plus Jakarta Sans` (Google Fonts), fallbacks: `system-ui`, `-apple-system`, `sans-serif`.
**Fonte para código**: `JetBrains Mono` (Google Fonts).

**Filosofia**: Limpo, profissional, acessível e responsivo. Foco em legibilidade e hierarquia visual clara.

## Tokens & Paleta de Cores (`tailwind.config.js`)

| Token | Hex / Classe | Descrição / Uso |
|-------|--------------|-----------------|
| `surface.bg` | `#F4F4F6` / `bg-[#F4F4F6]` | Fundo principal da aplicação e sidebar |
| `surface.card` | `#FFFFFF` / `bg-white` | Cards de mensagens do assistente, modais e sidebar items |
| `accent.emerald` | `#52C443` / `bg-emerald-500` | Botões primários, ícone do assistente, badges e destaques |
| `neutral.dark` | `#171717` / `bg-neutral-900` | Cards de mensagens do usuário, botões de ação e títulos |
| `border.default` | `#E5E5E5` / `border-neutral-200` | Bordas sutis dos cards e divisores |
| `text.primary` | `#171717` / `text-neutral-900` | Títulos e texto principal |
| `text.muted` | `#737373` / `text-neutral-500` | Subtítulos, timestamps e dados de suporte |

## Convenções de Componentes

### 1. Header (`ChatHeader.tsx`)
- Pílula de status do sistema: `bg-white/80 backdrop-blur-md rounded-full shadow-xs border border-neutral-200/80`.
- Seletor de modelos: Dropdown integrado com indicador visual de status ativo (`emerald-500`).

### 2. Mensagens (`MessageList.tsx`)
- **Usuário**: Card escuro `bg-neutral-900 text-white rounded-2xl rounded-tr-xs p-4 shadow-sm max-w-2xl ml-auto`.
- **Assistente**: Card branco `bg-white text-neutral-900 border border-neutral-200/80 rounded-2xl rounded-tl-xs p-5 shadow-sm max-w-3xl`.
- **Fontes (SourceBadges)**: Chips categorizados em tons pastel (Câmara: azul, Senado: verde, TSE: roxo, FactCheck: amarelo).

### 3. Sugestões (`SuggestionGrid.tsx`)
- Faixa horizontal com scroll oculta `no-scrollbar flex gap-2 overflow-x-auto`.
- Botões de sugestão estilo pílula `bg-white hover:bg-neutral-100 border border-neutral-200 rounded-full px-4 py-2 text-xs font-semibold text-neutral-700 shadow-2xs`.

### 4. Input (`App.tsx`)
- Container flutuante arredondado `bg-white border border-neutral-200/90 focus-within:border-emerald-500 focus-within:ring-2 focus-within:ring-emerald-500/20 rounded-2xl shadow-md p-2`.

## Modais (`IntroModal.tsx`)
- Card modal centralizado `bg-white rounded-3xl border border-neutral-200 shadow-2xl p-8 max-w-2xl` com fundo desfocado (`backdrop-blur-xs`).
