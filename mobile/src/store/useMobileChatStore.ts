import { create } from 'zustand';
import { sendChatMessage, SourceObject } from '../services/api';

export interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  sources?: SourceObject[];
  timestamp: string;
}

interface MobileChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (query: string) => Promise<void>;
  clearMessages: () => void;
}

export const useMobileChatStore = create<MobileChatState>((set) => ({
  messages: [
    {
      id: 'welcome',
      sender: 'bot',
      text: 'Olá! Sou o assistente de inteligência política e análise legislativa. Como posso te ajudar hoje?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ],
  isLoading: false,
  error: null,

  sendMessage: async (query: string) => {
    if (!query.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    try {
      const response = await sendChatMessage(query);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: response.answer,
        sources: response.sources,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      set((state) => ({
        messages: [...state.messages, botMessage],
        isLoading: false,
      }));
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.message || 'Falha ao obter resposta do servidor.',
      });
    }
  },

  clearMessages: () => {
    set({
      messages: [],
      error: null,
    });
  },
}));
