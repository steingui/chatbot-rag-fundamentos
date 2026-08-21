import { useState, useRef, useEffect } from 'react';
import { Send, Trash2, FileText, ExternalLink, Terminal, Loader2 } from 'lucide-react';
import './App.css';

const API_URL = 'https://chatbot-rag-api-q2k5.onrender.com/chat';

const INITIAL_MSG = '> Sessão iniciada. Sistema conectado à Câmara dos Deputados, TSE (DivulgaCand) e agências de fact-checking.\n\nComo posso te ajudar?';

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
  const [messages, setMessages] = useState<Message[]>([
    { id: '0', role: 'bot', content: INITIAL_MSG, timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const sessionId = useRef(`sess-${Math.random().toString(36).substring(2, 9)}`);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const sendMessage = async (query: string): Promise<{ answer: string; sources: Source[] }> => {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId.current, query })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || isLoading) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: query, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const data = await sendMessage(query);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: data.answer,
        sources: data.sources,
        timestamp: new Date()
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: '> ERRO: Falha ao conectar com a API. Verifique a conexão e tente novamente.',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleClear = () => {
    sessionId.current = `sess-${Math.random().toString(36).substring(2, 9)}`;
    setMessages([{ id: Date.now().toString(), role: 'bot', content: '> Contexto limpo. Nova sessão iniciada: ' + sessionId.current, timestamp: new Date() }]);
    inputRef.current?.focus();
  };

  const handleSummarize = async () => {
    const history = messages
      .filter(m => m.role === 'user')
      .map(m => m.content)
      .join(' | ');

    if (!history) return;

    setIsSummarizing(true);
    try {
      const data = await sendMessage(
        `Faça um resumo conciso e estruturado (em tópicos) das perguntas e temas desta conversa até agora: "${history}"`
      );
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'bot',
        content: '📋 **Resumo da conversa:**\n\n' + data.answer,
        timestamp: new Date()
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'bot',
        content: '> ERRO ao gerar resumo.',
        timestamp: new Date()
      }]);
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

        <div className="sidebar-section">
          <span className="sidebar-label">// sessão ativa</span>
          <code className="session-id">{sessionId.current}</code>
        </div>

        <div className="sidebar-actions">
          <button className="sidebar-btn" onClick={handleSummarize} disabled={isSummarizing || messages.length < 2}>
            {isSummarizing ? <Loader2 size={14} className="spin" /> : <FileText size={14} />}
            {isSummarizing ? 'gerando...' : 'resumir conversa'}
          </button>

          <button className="sidebar-btn danger" onClick={handleClear}>
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
            <span>rag-assistant</span>
          </div>
          <div className="model-badge">nvidia/nemotron-30b · free</div>
        </header>

        <main className="messages-area">
          {messages.map((msg) => (
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
                    <div
                      className="bot-text"
                      dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                    />
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="sources-row">
                        <span className="sources-label">// fontes:</span>
                        {msg.sources.map((s, i) =>
                          s.url ? (
                            <a key={i} href={s.url} target="_blank" rel="noopener noreferrer" className="source-chip" title={s.raw_file}>
                              <ExternalLink size={10} />
                              {s.label}
                            </a>
                          ) : (
                            <span key={i} className="source-chip no-link" title={s.raw_file}>
                              {s.label}
                            </span>
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
          <p className="input-hint">Enter para enviar · respostas baseadas em dados oficiais indexados</p>
        </div>
      </div>
    </div>
  );
}
