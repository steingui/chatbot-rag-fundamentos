import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Trash2, FileText, ExternalLink, Terminal, Loader2, Plus, MessageSquare, Cpu } from 'lucide-react';
import { parse } from 'marked';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'https://chatbot-rag-api-q2k5.onrender.com/chat';
const SUGGESTION_API_URL = API_URL.replace(/\/chat$/, '/suggestions');
const MAX_SESSIONS = 5;

const FREE_MODELS = [
  { id: 'nvidia/nemotron-3-nano-30b-a3b:free', label: 'nvidia/nemotron-30b · free' },
  { id: 'meta-llama/llama-3.3-70b-instruct:free', label: 'llama-3.3-70b · free' },
  { id: 'deepseek/deepseek-r1:free', label: 'deepseek-r1 · free' },
  { id: 'google/gemini-2.0-flash-exp:free', label: 'gemini-2.0-flash · free' },
  { id: 'qwen/qwen-2.5-72b-instruct:free', label: 'qwen-2.5-72b · free' }
];

type SuggestionItem = {
  prompt: string;
  count: number;
};

type Source = {
  type: string;
  label: string;
  url?: string;
  raw_file: string;
};

type Message = {
  id: string;
  role: 'user' | 'bot';
  content: string;
  sources?: Source[];
  timestamp: Date;
};

type Session = {
  id: string;     // session_id enviado para o backend
  label: string;  // título exibido (primeira pergunta)
  messages: Message[];
  createdAt: Date;
};

const newSessionId = () => `sess-${Math.random().toString(36).substring(2, 9)}`;

const makeSession = (index: number): Session => ({
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

function formatMarkdown(text: string): string {
  try {
    return parse(text, { gfm: true, breaks: true }) as string;
  } catch {
    return text;
  }
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([makeSession(0)]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState(FREE_MODELS[0].id);
  const [isLoading, setIsLoading] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([
    { prompt: 'Resuma a PEC 45/2019 e a reforma tributária', count: 24 },
    { prompt: 'Como os deputados votaram sobre o arcabouço fiscal?', count: 18 },
    { prompt: 'Quais bens foram declarados nas eleições recentes pelo TSE?', count: 12 },
    { prompt: 'O que a agência Lupa checou sobre imposto de renda?', count: 8 }
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const activeSession = sessions[activeIdx];

  const fetchSuggestions = useCallback(async () => {
    try {
      const res = await fetch(SUGGESTION_API_URL);
      if (res.ok) {
        const data = await res.json();
        if (data.suggestions && data.suggestions.length > 0) {
          setSuggestions(data.suggestions);
        }
      }
    } catch (e) {
      console.warn('Usando sugestões offline/fallback:', e);
    }
  }, []);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeSession?.messages, isLoading]);

  // Quando troca de aba, foca o input
  useEffect(() => {
    inputRef.current?.focus();
  }, [activeIdx]);

  const updateSession = useCallback((idx: number, updater: (s: Session) => Session) => {
    setSessions(prev => prev.map((s, i) => i === idx ? updater(s) : s));
  }, []);

  const sendToAPI = async (sessionId: string, query: string, model: string) => {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, query, model })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json() as Promise<{ answer: string; sources: Source[] }>;
  };

  const executeQuery = async (queryText: string) => {
    const query = queryText.trim();
    if (!query || isLoading) return;

    const capturedIdx = activeIdx;
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date()
    };

    // Atualiza label da sessão na primeira pergunta real
    setSessions(prev => prev.map((s, i) => {
      if (i !== capturedIdx) return s;
      const isFirstUserMsg = s.messages.filter(m => m.role === 'user').length === 0;
      return {
        ...s,
        label: isFirstUserMsg ? query.slice(0, 30) + (query.length > 30 ? '…' : '') : s.label,
        messages: [...s.messages, userMsg]
      };
    }));

    setInput('');
    setIsLoading(true);

    try {
      const data = await sendToAPI(sessions[capturedIdx].id, query, selectedModel);
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: data.answer,
        sources: data.sources,
        timestamp: new Date()
      };
      updateSession(capturedIdx, s => ({ ...s, messages: [...s.messages, botMsg] }));
    } catch {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: '> **Erro de conexão**: Não foi possível consultar o backend. Tente novamente em instantes.',
        timestamp: new Date()
      };
      updateSession(capturedIdx, s => ({ ...s, messages: [...s.messages, errorMsg] }));
    } finally {
      setIsLoading(false);
      fetchSuggestions();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeQuery(input);
  };

  const handleNewSession = () => {
    if (sessions.length >= MAX_SESSIONS) return;
    const newIdx = sessions.length;
    setSessions(prev => [...prev, makeSession(newIdx)]);
    setActiveIdx(newIdx);
  };

  const handleCloseSession = (idxToClose: number) => {
    if (sessions.length === 1) return;
    setSessions(prev => prev.filter((_, i) => i !== idxToClose));
    if (activeIdx >= idxToClose && activeIdx > 0) {
      setActiveIdx(prev => prev - 1);
    }
  };

  const handleClearContext = () => {
    const freshSession: Session = {
      id: newSessionId(),
      label: `Sessão ${activeIdx + 1}`,
      messages: [{
        id: 'init',
        role: 'bot',
        content: `> Contexto limpo. Nova sessão \`${activeSession.label}\` pronta.`,
        timestamp: new Date()
      }],
      createdAt: new Date()
    };
    updateSession(activeIdx, () => freshSession);
  };

  const handleSummarize = async () => {
    if (isSummarizing || activeSession.messages.length < 2) return;
    setIsSummarizing(true);

    const userQuestions = activeSession.messages
      .filter(m => m.role === 'user')
      .map(m => m.content)
      .join('; ');

    const promptText = `Resuma os principais pontos discutidos nesta sessão até agora. Tópicos abordados: ${userQuestions}`;

    try {
      const data = await sendToAPI(activeSession.id, promptText, selectedModel);
      const summaryMsg: Message = {
        id: Date.now().toString(),
        role: 'bot',
        content: `**📋 Resumo da Sessão (${activeSession.label}):**\n\n${data.answer}`,
        sources: data.sources,
        timestamp: new Date()
      };
      updateSession(activeIdx, s => ({ ...s, messages: [...s.messages, summaryMsg] }));
    } catch {
      // ignora erro no resumo
    } finally {
      setIsSummarizing(false);
    }
  };

  return (
    <div className="layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Terminal size={18} className="accent" />
          <span>rag<span className="accent">_politico</span></span>
        </div>

        <div className="sessions-section">
          <div className="sidebar-section-header">
            <span className="sidebar-label">Sessões ({sessions.length}/{MAX_SESSIONS})</span>
            <button
              className="new-session-btn"
              onClick={handleNewSession}
              disabled={sessions.length >= MAX_SESSIONS}
              title="Nova Sessão"
            >
              <Plus size={14} />
            </button>
          </div>

          <ul className="sessions-list">
            {sessions.map((sess, idx) => (
              <li
                key={sess.id}
                className={`session-item ${idx === activeIdx ? 'active' : ''}`}
                onClick={() => setActiveIdx(idx)}
              >
                <MessageSquare size={12} className="session-icon" />
                <span className="session-label">{sess.label}</span>
                {sessions.length > 1 && (
                  <button
                    className="session-close"
                    onClick={e => { e.stopPropagation(); handleCloseSession(idx); }}
                    title="Fechar sessão"
                  >×</button>
                )}
              </li>
            ))}
          </ul>
        </div>

        {/* ACTIONS */}
        <div className="sidebar-actions">
          <button className="sidebar-btn" onClick={handleSummarize} disabled={isSummarizing || activeSession.messages.length < 2}>
            {isSummarizing ? <Loader2 size={14} className="spin" /> : <FileText size={14} />}
            {isSummarizing ? 'gerando...' : 'resumir conversa'}
          </button>

          <button className="sidebar-btn danger" onClick={handleClearContext}>
            <Trash2 size={14} />
            limpar contexto
          </button>
        </div>

        <div className="sidebar-footer">
          <div className="status-dot"></div>
          <span>API conectada</span>
        </div>
      </aside>

      {/* CHAT PANEL */}
      <div className="chat-panel">
        <header className="chat-header">
          <div className="header-title">
            <span className="prompt-prefix">~/politica</span>
            <span className="header-sep">$</span>
            <span>{activeSession.label}</span>
          </div>

          <div className="model-select-wrapper">
            <Cpu size={13} className="accent" />
            <select
              className="model-select"
              value={selectedModel}
              onChange={e => setSelectedModel(e.target.value)}
              title="Selecione o modelo OpenRouter Free Tier"
            >
              {FREE_MODELS.map(m => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
        </header>

        <main className="messages-area">
          {activeSession.messages.map((msg) => (
            <div key={msg.id} className={`message-block ${msg.role}`}>
              {msg.role === 'user' ? (
                <div className="user-row">
                  <span className="user-prefix">you@rag:~$</span>
                  <p className="user-text">{msg.content}</p>
                  <span className="msg-time">{formatTime(msg.timestamp)}</span>
                </div>
              ) : (
                <div className="bot-row">
                  <div className="bot-prefix-col">
                    <span className="bot-tag">AI</span>
                  </div>
                  <div className="bot-content">
                    <div className="bot-text" dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }} />
                    {msg.id === 'init' && (
                      <div className="suggestions-block">
                        <span className="suggestions-title">// sugestões de consulta:</span>
                        <div className="suggestions-grid">
                          {suggestions.map((item, idx) => (
                            <button
                              key={idx}
                              className="suggestion-card"
                              onClick={() => executeQuery(item.prompt)}
                              disabled={isLoading}
                            >
                              <span className="suggestion-icon">›</span>
                              <span className="suggestion-text">{item.prompt}</span>
                              <span className="suggestion-badge" title={`${item.count} consultas efetuadas`}>{item.count}x</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="sources-row">
                        <span className="sources-label">// fontes:</span>
                        {Array.from(new Map(msg.sources.map(s => [`${s.label}-${s.url || ''}`, s])).values()).map((s, i) =>
                          s.url ? (
                            <a key={i} href={s.url} target="_blank" rel="noopener noreferrer" className="source-chip" title={s.raw_file}>
                              <ExternalLink size={10} />{s.label}
                            </a>
                          ) : (
                            <span key={i} className="source-chip no-link" title={s.raw_file}>{s.label}</span>
                          )
                        )}
                      </div>
                    )}
                    <span className="msg-time">{formatTime(msg.timestamp)}</span>
                  </div>
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="message-block bot">
              <div className="bot-row">
                <div className="bot-prefix-col"><span className="bot-tag">AI</span></div>
                <div className="typing-indicator">
                  <span className="typing-cursor">_</span>
                  <span className="typing-cursor">_</span>
                  <span className="typing-cursor">_</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </main>

        <div className="input-area">
          <form onSubmit={handleSubmit} className="input-form">
            <span className="input-prefix">$</span>
            <input
              ref={inputRef}
              type="text"
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="pergunte sobre pautas, votações, bens ou fact-checking..."
              disabled={isLoading}
              autoFocus
            />
            <button type="submit" className="send-btn" disabled={!input.trim() || isLoading}>
              <Send size={16} />
            </button>
          </form>
          <p className="input-hint">Enter para enviar · sessão: <code>{activeSession.id}</code></p>
        </div>
      </div>
    </div>
  );
}
