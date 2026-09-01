# 🏛️ Chatbot RAG Frontend (v2)

Interface web moderna desenvolvida com **React 18**, **TypeScript**, **Vite**, **Tailwind CSS v3** e **Zustand**.

## 🎨 Design System v2 (Elera UI)

- **Superfície**: `#F4F4F6` (Off-white profissional).
- **Tipografia**: `Plus Jakarta Sans` (Google Fonts).
- **Acentos**: Esmeralda (`#52C443` / `bg-emerald-500`) e Anthracite.
- **Componentes**:
  - `ChatHeader`: Indicadores de status e seletor de modelos em pílulas.
  - `SessionSidebar`: Cards arredondados `rounded-2xl`, pílulas de sessões ativas e ações rápidas.
  - `SuggestionGrid`: Faixa de sugestões em pílulas com scroll horizontal suave.
  - `MessageList`: Virtualizado via `@tanstack/react-virtual`, mensagens do bot em cards brancos elevados com badges de fontes categorizados.
  - `IntroModal`: Modal educativo com informações de transparência e busca vetorial.

## 🚀 Comandos

```bash
# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev

# Executar testes (Vitest)
npm run test

# Gerar build de produção
npm run build
```
