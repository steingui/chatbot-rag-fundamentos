import { useEffect, useRef } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { useChatStore } from './store/useChatStore';
import { SessionSidebar } from './components/SessionSidebar';
import { ChatHeader } from './components/ChatHeader';
import { MessageList } from './components/MessageList';
import { SuggestionGrid } from './components/SuggestionGrid';
import './App.css';

export default function App() {
  const {
    input,
    setInput,
    isLoading,
    fontSize,
    fetchSuggestions,
    sendMessageStream
  } = useChatStore();

  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  useEffect(() => {
    document.documentElement.style.setProperty('--chat-font-size', `${fontSize}px`);
    document.documentElement.style.fontSize = `${fontSize}px`;
  }, [fontSize]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessageStream(input);
  };

  return (
    <div className="layout">
      <SessionSidebar />

      <main className="chat-panel">
        <ChatHeader />
        <SuggestionGrid />
        <MessageList />

        <footer className="input-area">
          <form onSubmit={handleSubmit} className="input-form">
            <span className="input-prefix">&gt;</span>
            <input
              ref={inputRef}
              type="text"
              className="chat-input"
              placeholder="Pergunte sobre PECs, projetos de lei, votações ou checagens..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              className="send-btn"
              disabled={!input.trim() || isLoading}
            >
              {isLoading ? (
                <Loader2 size={16} className="spin-icon spin" />
              ) : (
                <Send size={16} />
              )}
            </button>
          </form>
        </footer>
      </main>
    </div>
  );
}
