import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Trash2, FileText, ExternalLink, Terminal, Loader2, Plus, MessageSquare } from 'lucide-react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'https://chatbot-rag-api-q2k5.onrender.com/chat';
const MAX_SESSIONS = 5;

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
    content: `> Sessão ${index + 1} iniciada. Sistema conectado à Câmara dos Deputados, TSE e agências de fact-checking.\n\nComo posso te ajudar?`,
    timestamp: new Date()
  }],
  createdAt: new Date()
});

function formatMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>');
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([makeSession(0)]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const activeSession = sessions[activeIdx];

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

  const sendToAPI = async (sessionId: string, query: string) => {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, query })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json() as Promise<{ answer: string; sources: Source[] }>;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = input.trim();
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
      const data = await sendToAPI(sessions[capturedIdx].id, query);
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: data.answer,
        sources: data.sources,
        timestamp: new Date()
      };
      updateSession(capturedIdx, s => ({ ...s, messages: [...s.messages, botMsg] }));
    } catch {
      updateSession(capturedIdx, s => ({
        ...s,
        messages: [...s.messages, {
          id: (Date.now() + 1).toString(),
          role: 'bot',
          content: '> ERRO: Falha ao conectar com a API. Tente novamente.',
          timestamp: new Date()
        }]
      }));
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleNewSession = () => {
    if (sessions.length >= MAX_SESSIONS) return;
    const newIdx = sessions.length;
    setSessions(prev => [...prev, makeSession(newIdx)]);
    setActiveIdx(newIdx);
  };

  const handleCloseSession = (idx: number) => {
    if (sessions.length === 1) {
      // Se é a última, reseta ela ao invés de fechar
      setSessions([makeSession(0)]);
      setActiveIdx(0);
      return;
    }
    setSessions(prev => prev.filter((_, i) => i !== idx));
    setActiveIdx(prev => Math.min(prev, sessions.length - 2));
  };

  const handleClearContext = () => {
    const newSess = makeSession(activeIdx);
    newSess.label = activeSession.label; // mantém o label
    updateSession(activeIdx, () => newSess);
    inputRef.current?.focus();
  };

  const handleSummarize = async () => {
    const userQueries = activeSession.messages
      .filter(m => m.role === 'user')
      .map(m => m.content)
      .join(' | ');
    if (!userQueries) return;

    setIsSummarizing(true);
    const capturedIdx = activeIdx;
    try {
      const data = await sendToAPI(
        activeSession.id,
        `Faça um resumo conciso em tópicos das perguntas e temas desta conversa: "${userQueries}"`
      );
      updateSession(capturedIdx, s => ({
        ...s,
        messages: [...s.messages, {
          id: Date.now().toString(),
          role: 'bot',
          content: '📋 **Resumo da conversa:**\n\n' + data.answer,
          timestamp: new Date()
        }]
      }));
    } catch {
      updateSession(capturedIdx, s => ({
        ...s,
        messages: [...s.messages, {
          id: Date.now().toString(),
          role: 'bot',
          content: '> ERRO ao gerar resumo.',
          timestamp: new Date()
        }]
      }));
    } finally {
      setIsSummarizing(false);
    }
  };

  return (
    <div className="layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Terminal size={18} />
          <span>rag<span className="accent">_politico</span></span>
        </div>

        {/* SESSIONS LIST */}
        <div className="sessions-section">
          <div className="sidebar-section-header">
            <span className="sidebar-label">// sessões ({sessions.length}/{MAX_SESSIONS})</span>
            <button
              className="new-session-btn"
              onClick={handleNewSession}
              disabled={sessions.length >= MAX_SESSIONS}
              title={sessions.length >= MAX_SESSIONS ? 'Limite de 5 sessões atingido' : 'Nova sessão'}
            >
              <Plus size={12} />
            </button>
          </div>

          <ul className="sessions-list">
            {sessions.map((sess, idx) => (
              <li
                key={sess.id}
                className={`session-item ${idx === activeIdx ? 'active' : ''}`}
                onClick={() => setActiveIdx(idx)}
              >
                <MessageSquare size={11} className="session-icon" />
                <span className="session-label">{sess.label}</span>
                <button
                  className="session-close"
                  onClick={e => { e.stopPropagation(); handleCloseSession(idx); }}
                  title="Fechar sessão"
                >×</button>
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
          <div className="model-badge">nvidia/nemotron-30b · free</div>
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
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="sources-row">
                        <span className="sources-label">// fontes:</span>
                        {msg.sources.map((s, i) =>
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
