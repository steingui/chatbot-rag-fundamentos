import { create } from 'zustand';
import { parse } from 'marked';
import DOMPurify from 'dompurify';

export const API_URL = import.meta.env.VITE_API_URL || 'https://chatbot-rag-api-q2k5.onrender.com/chat';
export const STREAM_API_URL = API_URL.endsWith('/chat') ? `${API_URL}/stream` : `${API_URL}/chat/stream`;
export const SUGGESTION_API_URL = API_URL.replace(/\/chat$/, '/suggestions');
export const MAX_SESSIONS = 5;

export const FREE_MODELS = [
  { id: 'nvidia/nemotron-3-nano-30b-a3b:free', label: 'nvidia/nemotron-30b · free' },
  { id: 'meta-llama/llama-3.3-70b-instruct:free', label: 'llama-3.3-70b · free' },
  { id: 'deepseek/deepseek-r1:free', label: 'deepseek-r1 · free' },
  { id: 'google/gemini-2.0-flash-exp:free', label: 'gemini-2.0-flash · free' },
  { id: 'qwen/qwen-2.5-72b-instruct:free', label: 'qwen-2.5-72b · free' }
];

export type SuggestionItem = {
  prompt: string;
  count: number;
};

export type Source = {
  type: string;
  label: string;
  url?: string;
  raw_file: string;
};

export type Message = {
  id: string;
  role: 'user' | 'bot';
  content: string;
  sources?: Source[];
  timestamp: Date;
};

export type Session = {
  id: string;
  label: string;
  messages: Message[];
  createdAt: Date;
};

const newSessionId = () => `sess-${Math.random().toString(36).substring(2, 9)}`;

export const makeSession = (index: number): Session => ({
  id: newSessionId(),
  label: `Sessão ${index + 1}`,
  messages: [{
    id: 'init',
    role: 'bot',
    content: `> Sessão ${index + 1} iniciada. Sistema conectado à Câmara dos Deputados, Senado Federal, TSE e CGU.\n\nComo posso te ajudar?`,
    timestamp: new Date()
  }],
  createdAt: new Date()
});

export function formatMarkdown(text: string): string {
  try {
    const rawHtml = parse(text, { gfm: true, breaks: true }) as string;
    return DOMPurify.sanitize(rawHtml, {
      ADD_ATTR: ['target', 'rel']
    });
  } catch {
    return text;
  }
}

export function formatTime(date: Date): string {
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

interface ChatState {
  sessions: Session[];
  activeIdx: number;
  input: string;
  selectedModel: string;
  isLoading: boolean;
  suggestions: SuggestionItem[];
  
  // Actions
  setInput: (input: string) => void;
  setSelectedModel: (model: string) => void;
  setActiveIdx: (idx: number) => void;
  addSession: () => void;
  closeSession: (idx: number) => void;
  clearActiveSession: () => void;
  setSuggestions: (suggestions: SuggestionItem[]) => void;
  fetchSuggestions: () => Promise<void>;
  sendMessageStream: (queryText: string) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [makeSession(0)],
  activeIdx: 0,
  input: '',
  selectedModel: FREE_MODELS[0].id,
  isLoading: false,
  suggestions: [
    { prompt: 'Resuma a PEC 45/2019 e a reforma tributária', count: 24 },
    { prompt: 'Como os deputados votaram sobre o arcabouço fiscal?', count: 18 },
    { prompt: 'Quais bens foram declarados nas eleições recentes pelo TSE?', count: 12 },
    { prompt: 'O que a agência Lupa checou sobre imposto de renda?', count: 8 }
  ],

  setInput: (input) => set({ input }),
  setSelectedModel: (selectedModel) => set({ selectedModel }),
  setActiveIdx: (activeIdx) => set({ activeIdx }),

  addSession: () => {
    const { sessions } = get();
    if (sessions.length >= MAX_SESSIONS) return;
    const newIdx = sessions.length;
    set({
      sessions: [...sessions, makeSession(newIdx)],
      activeIdx: newIdx
    });
  },

  closeSession: (idxToClose) => {
    const { sessions, activeIdx } = get();
    if (sessions.length === 1) return;
    const newSessions = sessions.filter((_, i) => i !== idxToClose);
    let newActive = activeIdx;
    if (activeIdx >= idxToClose && activeIdx > 0) {
      newActive = activeIdx - 1;
    }
    set({ sessions: newSessions, activeIdx: newActive });
  },

  clearActiveSession: () => {
    const { sessions, activeIdx } = get();
    const freshSession: Session = {
      id: newSessionId(),
      label: `Sessão ${activeIdx + 1}`,
      messages: [{
        id: 'init',
        role: 'bot',
        content: `> Sessão ${activeIdx + 1} reiniciada. Sistema limpo.\n\nComo posso te ajudar?`,
        timestamp: new Date()
      }],
      createdAt: new Date()
    };
    const updated = [...sessions];
    updated[activeIdx] = freshSession;
    set({ sessions: updated });
  },

  setSuggestions: (suggestions) => set({ suggestions }),

  fetchSuggestions: async () => {
    try {
      const res = await fetch(SUGGESTION_API_URL);
      if (res.ok) {
        const data = await res.json();
        if (data.suggestions && data.suggestions.length > 0) {
          set({ suggestions: data.suggestions });
        }
      }
    } catch (e) {
      console.warn('Usando sugestões offline/fallback:', e);
    }
  },

  sendMessageStream: async (queryText: string) => {
    const query = queryText.trim();
    const { isLoading, activeIdx, sessions, selectedModel, fetchSuggestions } = get();
    if (!query || isLoading) return;

    const capturedIdx = activeIdx;
    const currentSession = sessions[capturedIdx];
    if (!currentSession) return;

    set({ isLoading: true, input: '' });

    // Atualiza o título da sessão se for a primeira pergunta
    const userMessageCount = currentSession.messages.filter(m => m.role === 'user').length;
    if (userMessageCount === 0) {
      const newLabel = query.length > 25 ? `${query.substring(0, 25)}...` : query;
      const updated = [...get().sessions];
      updated[capturedIdx] = { ...updated[capturedIdx], label: newLabel };
      set({ sessions: updated });
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date()
    };

    const botMsgId = (Date.now() + 1).toString();
    const botMsg: Message = {
      id: botMsgId,
      role: 'bot',
      content: '',
      sources: [],
      timestamp: new Date()
    };

    // Adiciona mensagem do usuário e mensagem placeholder do bot
    let updatedSessions = [...get().sessions];
    updatedSessions[capturedIdx] = {
      ...updatedSessions[capturedIdx],
      messages: [...updatedSessions[capturedIdx].messages, userMsg, botMsg]
    };
    set({ sessions: updatedSessions });

    let accumulatedContent = '';
    let accumulatedSources: Source[] = [];

    try {
      const res = await fetch(STREAM_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSession.id,
          query,
          model: selectedModel
        })
      });

      if (!res.ok || !res.body) {
        // Fallback HTTP POST /chat tradicional
        const fallbackRes = await fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: currentSession.id, query, model: selectedModel })
        });
        if (!fallbackRes.ok) throw new Error(`HTTP ${fallbackRes.status}`);
        const data = await fallbackRes.json();
        
        updatedSessions = [...get().sessions];
        const msgs = updatedSessions[capturedIdx].messages.map(m => 
          m.id === botMsgId ? { ...m, content: data.answer, sources: data.sources } : m
        );
        updatedSessions[capturedIdx] = { ...updatedSessions[capturedIdx], messages: msgs };
        set({ sessions: updatedSessions });
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const dataStr = trimmed.replace(/^data:\s*/, '');
          if (dataStr === '[DONE]') break;

          try {
            const eventData = JSON.parse(dataStr);
            if (eventData.type === 'sources') {
              accumulatedSources = eventData.sources || [];
            } else if (eventData.type === 'token') {
              accumulatedContent += eventData.token || '';
            }

            // Atualização reativa de tokens no estado
            updatedSessions = [...get().sessions];
            const msgs = updatedSessions[capturedIdx].messages.map(m => 
              m.id === botMsgId ? { ...m, content: accumulatedContent, sources: accumulatedSources } : m
            );
            updatedSessions[capturedIdx] = { ...updatedSessions[capturedIdx], messages: msgs };
            set({ sessions: updatedSessions });
          } catch {
            // Ignora JSON parcial
          }
        }
      }
    } catch (e) {
      console.error('Erro no streaming:', e);
      updatedSessions = [...get().sessions];
      const msgs = updatedSessions[capturedIdx].messages.map(m => 
        m.id === botMsgId ? {
          ...m,
          content: accumulatedContent || '> **Erro de conexão**: Não foi possível consultar o backend em tempo real.'
        } : m
      );
      updatedSessions[capturedIdx] = { ...updatedSessions[capturedIdx], messages: msgs };
      set({ sessions: updatedSessions });
    } finally {
      set({ isLoading: false });
      fetchSuggestions();
    }
  }
}));
