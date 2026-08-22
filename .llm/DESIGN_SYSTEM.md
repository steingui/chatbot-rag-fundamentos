# Design System — RAG Político

## Identidade Visual

**Conceito**: Interface de terminal hacker — fundo escuro, tipografia monospace,
acentos neon verdes, estética que remete a linha de comando.

**Fonte primária**: `JetBrains Mono` (Google Fonts), fallbacks: `Fira Code`, `Cascadia Code`, `monospace`.

**Filosofia**: Minimalista e funcional. Sem decorações supérfluas, animações sutis, informação densa.

## Tokens CSS (`theme/tokens.css`)

```css
:root {
  /* Palette */
  --bg:          #0b0c0e;     /* Fundo principal (quase preto azulado) */
  --surface:     #111215;     /* Superfícies elevadas (sidebar, header) */
  --surface-2:   #16181d;     /* Superfícies secundárias (inputs, cards) */
  --border:      #23262d;     /* Bordas padrão */
  --border-hi:   #343842;     /* Bordas enfatizadas */
  --text:        #e6e8ec;     /* Texto primário */
  --muted:       #6b7280;     /* Texto secundário / labels */
  --accent:      #00ff88;     /* Verde neon principal (CTAs, ativo, user prompt) */
  --accent-dim:  rgba(0,255,136,0.1);   /* Background de accent sutil */
  --accent-glow: rgba(0,255,136,0.08);  /* Glow/shadow de accent */
  --gold:        #ffbd2e;     /* Dourado (bot header, badges de contagem) */
  --gold-dim:    rgba(255,189,46,0.12); /* Background gold sutil */
  --red:         #ff5f57;     /* Vermelho (ações destrutivas) */
  --red-dim:     rgba(255,95,87,0.12);  /* Background red sutil */
  --green:       #28ca41;     /* Verde status (dot online) */

  /* Typography */
  --font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;

  /* Radii */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;

  /* Transitions */
  --transition: all 0.15s ease;
}
```

## Tokens TypeScript (`theme/tokens.ts`)

Mesmos valores em formato tipado (`as const`) para uso programático em componentes
caso necessário. Exporta `tokens` e `ThemeTokens` type.

## Convenções de Cor por Contexto

| Contexto | Cor | Variável |
|----------|-----|----------|
| Prompt do usuário (header) | Verde neon | `--accent` |
| Header do bot | Dourado | `--gold` (#ffbd2e) |
| Badge de contagem (sugestões) | Dourado sobre fundo dim | `--gold` / `--gold-dim` |
| Botão destrutivo (Limpar Sessão) | Vermelho | `--red` |
| Sessão ativa (sidebar) | Verde com borda accent | `--accent` + `--accent-dim` bg |
| Status online (footer dot) | Verde brilhante com pulse | `--green` |
| Texto de timestamp | Muted | `--muted` |
| Source chips (RAG) | Verde sobre accent-dim | `--accent` bg/border |
| Source chips (sem link) | Muted sobre surface-2 | `--muted` bg |

## Elementos Visuais Chave

### Brand (Sidebar)
```
[>_] rag_politico v1.0
```
- `>_` em caixa accent com borda accent (simula cursor de terminal)
- Nome em bold, versão em muted alinhada à direita

### Prompt do Usuário
```
you@rag:~$
```
- Cor: `--accent` (#00ff88)
- Simula prompt de terminal Unix

### Header do Bot
```
⚡ ASSISTENTE (RAG)
```
- ⚡ e texto em `--gold` (#ffbd2e)
- Caps com letter-spacing

### Sessão Ativa
```
▢ Nome da sessão
```
- `▢` para ativa, `◯` para inativa
- Background: `rgba(0, 255, 136, 0.08)` com borda accent

### Input
```
> [input field]  [send icon]
```
- Prefixo `>` em accent
- Caret color: accent
- Focus: borda accent com glow sutil

## Layout

```
┌─── 240px ────┬──── flex: 1 ──────────────────────────┐
│              │  HEADER (ChatHeader + ModelSelector)   │
│   SIDEBAR    │  SUGGESTIONS (SuggestionGrid)          │
│  (sessions)  │  MESSAGES (MessageList, scroll)        │
│              │  INPUT (footer form)                   │
└──────────────┴───────────────────────────────────────-┘
```

- Sidebar: `width: 240px`, `flex-shrink: 0`
- Chat panel: `flex: 1`
- Responsivo: sidebar oculta em `max-width: 680px`

## Animações

| Elemento | Animação | Duração |
|----------|----------|---------|
| Status dot (footer) | `pulse` (opacity 1→0.4→1) | 2s infinite |
| Send button (loading) | `spin` (rotate 360°) | 1s linear infinite |
| Hover/focus transitions | `all 0.15s ease` | 150ms |

## Scrollbar

```css
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
```
