import { useEffect, useRef } from 'react';
import { Send, Command, Square, RotateCcw } from 'lucide-react';
import { useChatStore } from './store/useChatStore';
import {
  SessionSidebar,
  ChatHeader,
  MessageList,
  SuggestionGrid,
  IntroModal
} from './components';

export default function App() {
  const {
    input,
    setInput,
    isLoading,
    fontSize,
    isSidebarOpen,
    sessions,
    activeIdx,
    fetchSuggestions,
    sendMessageStream,
    stopStream,
    editLastPrompt
  } = useChatStore();

  const inputRef = useRef<HTMLInputElement>(null);
  const currentSession = sessions[activeIdx];
  const hasMessages = currentSession?.messages?.some(m => m.role === 'user');

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
    <div className="flex h-screen w-screen bg-[#F4F4F6] text-neutral-900 font-sans overflow-hidden">
      <IntroModal />
      {isSidebarOpen && <SessionSidebar />}

      <main className="flex-1 flex flex-col h-full bg-[#F4F4F6] overflow-hidden min-w-0">
        <ChatHeader />
        <SuggestionGrid />
        <MessageList />

        <footer className="p-4 bg-[#F4F4F6] border-t border-neutral-200/60 flex flex-col items-center gap-2 shrink-0">
          <form
            onSubmit={handleSubmit}
            className="bg-white border border-neutral-200/90 focus-within:border-emerald-500 focus-within:ring-2 focus-within:ring-emerald-500/20 rounded-2xl shadow-md p-2 flex items-center gap-3 w-full max-w-4xl transition-all"
          >
            <div className="flex items-center justify-center pl-2 text-neutral-400">
              <Command size={16} />
            </div>
            
            <input
              ref={inputRef}
              type="text"
              className="flex-1 bg-transparent text-sm font-medium text-neutral-900 placeholder:text-neutral-400 focus:outline-none py-2"
              placeholder="Pergunte sobre PECs, projetos de lei, votações, TSE ou checagens de fatos..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />

            {!isLoading && hasMessages && (
              <button
                type="button"
                onClick={() => {
                  editLastPrompt();
                  inputRef.current?.focus();
                }}
                className="p-2.5 rounded-xl text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 transition-all cursor-pointer border border-neutral-200/60 flex items-center gap-1.5 text-xs font-semibold shrink-0"
                title="Editar e refazer o último prompt"
              >
                <RotateCcw size={14} />
                <span className="hidden sm:inline">Refazer último</span>
              </button>
            )}

            {isLoading ? (
              <button
                type="button"
                onClick={stopStream}
                className="bg-red-500 hover:bg-red-600 text-white font-bold p-3 rounded-xl transition-all shadow-sm flex items-center justify-center cursor-pointer shrink-0 animate-pulse"
                title="Pausar / Interromper resposta"
              >
                <Square size={16} fill="currentColor" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-40 text-neutral-900 font-bold p-3 rounded-xl transition-all shadow-sm flex items-center justify-center cursor-pointer shrink-0"
                title="Enviar pergunta"
              >
                <Send size={16} />
              </button>
            )}
          </form>
        </footer>
      </main>
    </div>
  );
}
