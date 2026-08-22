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

const LOCAL_STORAGE_KEY = 'rag_chat_sessions_v1';
const SUGGESTIONS_CACHE_KEY = 'rag_suggestions_cache_v1';
const SUGGESTIONS_TTL_MS = 5 * 60 * 1000; // 5 min TTL

const loadPersistedSessions = (): Session[] | null => {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed.map((s: any) => {
      const messages = (s.messages || []).map((m: any) => ({ ...m, timestamp: new Date(m.timestamp) }));
      const firstUserMsg = messages.find((m: any) => m.role === 'user');
      const label = firstUserMsg ? firstUserMsg.content : (s.label || '').replace(/\.\.\.$/, '');
      return {
        ...s,
        label,
        createdAt: new Date(s.createdAt),
        messages
      };
    });
  } catch {
    return null;
  }
};

const savePersistedSessions = (sessions: Session[]) => {
  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(sessions));
  } catch (e) {
    console.warn('Falha ao salvar sessoes no localStorage:', e);
  }
};

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: loadPersistedSessions() || [makeSession(0)],
  activeIdx: 0,
  input: '',
  selectedModel: FREE_MODELS[0].id,
  isLoading: false,
  suggestions: [
    { prompt: 'Quais senadores mais utilizaram a cota parlamentar (CEAPS)?', count: 32 },
    { prompt: 'Qual o resultado da votação 2580259-24 na Câmara dos Deputados?', count: 28 },
    { prompt: 'Quais os gastos da senadora Damares Alves na cota CEAPS?', count: 25 },
    { prompt: 'O que diz a checagem sobre o golpe da lista de CPFs com indenização de R$ 5 mil?', count: 21 },
    { prompt: 'Quais os detalhes da execução orçamentária da Emenda PIX nº 202581000001?', count: 19 },
    { prompt: 'Como votaram os senadores na votação do PLP 204 no Senado?', count: 16 },
    { prompt: 'Quais senadores tiveram reembolso de despesas de consumo no Senado em 2025?', count: 14 },
    { prompt: 'Como o deputado Carlos Zarattini votou na votação 2580259-24?', count: 12 }
  ],

  setInput: (input) => set({ input }),
  setSelectedModel: (selectedModel) => set({ selectedModel }),
  setActiveIdx: (activeIdx) => set({ activeIdx }),

  addSession: () => {
    const { sessions } = get();
    if (sessions.length >= MAX_SESSIONS) return;
    const newIdx = sessions.length;
    const updated = [...sessions, makeSession(newIdx)];
    set({ sessions: updated, activeIdx: newIdx });
    savePersistedSessions(updated);
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
    savePersistedSessions(newSessions);
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
    savePersistedSessions(updated);
  },

  setSuggestions: (suggestions) => set({ suggestions }),

  fetchSuggestions: async () => {
    // Cache Inteligente de Sugestões com TTL
    try {
      const cached = localStorage.getItem(SUGGESTIONS_CACHE_KEY);
      if (cached) {
        const { timestamp, data } = JSON.parse(cached);
        if (Date.now() - timestamp < SUGGESTIONS_TTL_MS && data?.length > 0) {
          set({ suggestions: data });
          return;
        }
      }
    } catch {
      // Ignora erro de parse do cache
    }

    try {
      const res = await fetch(SUGGESTION_API_URL);
      if (res.ok) {
        const data = await res.json();
        if (data.suggestions && data.suggestions.length > 0) {
          set({ suggestions: data.suggestions });
          try {
            localStorage.setItem(SUGGESTIONS_CACHE_KEY, JSON.stringify({
              timestamp: Date.now(),
              data: data.suggestions
            }));
          } catch {
            // Ignora erro de escrita
          }
        }
      }
    } catch (e) {
      console.warn('Usando sugestões offline/fallback:', e);
    }
  },

  sendMessageStream: async (queryText: string) => {
    const query = queryText.trim();
    const { isLoading, activeIdx, sessions, selectedModel, fetchSuggestions } = get();

    // Proteção Anti-Spam & Trava Concorrente Estrita
    if (!query || isLoading) return;

    const capturedIdx = activeIdx;
    const currentSession = sessions[capturedIdx];
    if (!currentSession) return;

    set({ isLoading: true, input: '' });

    // Atualiza o título da sessão se for a primeira pergunta
    const userMessageCount = currentSession.messages.filter(m => m.role === 'user').length;
    if (userMessageCount === 0) {
      const newLabel = query;
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
    savePersistedSessions(updatedSessions);

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
        savePersistedSessions(updatedSessions);
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
      savePersistedSessions(get().sessions);
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
      savePersistedSessions(updatedSessions);
    } finally {
      set({ isLoading: false });
      fetchSuggestions();
    }
  }
}));
