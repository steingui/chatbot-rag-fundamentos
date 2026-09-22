import { useEffect, useRef } from 'react';
import { Send, Command, Square, RotateCcw } from 'lucide-react';
import { useChatStore } from './store/useChatStore';
import {
  SessionSidebar,
  ChatHeader,
  MessageList,
  SuggestionGrid,
  DashboardCards,
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
    editLastPrompt,
    toggleSidebar
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
    <div className="flex h-screen w-screen bg-gray-50 text-gray-900 font-sans overflow-hidden">
      <IntroModal />

      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/20 lg:hidden"
          onClick={toggleSidebar}
          aria-hidden="true"
        />
      )}
      {isSidebarOpen && <SessionSidebar />}

      <main className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <ChatHeader />
        <SuggestionGrid />
        {hasMessages ? <MessageList /> : <DashboardCards />}

        <footer className="p-4 sm:p-5 flex flex-col items-center gap-2 shrink-0">
          <form
            onSubmit={handleSubmit}
            className="w-full max-w-4xl rounded-2xl bg-white border border-gray-200 shadow-sm p-2 sm:p-2.5 flex items-center gap-3 focus-within:border-emerald-500 focus-within:ring-4 focus-within:ring-emerald-500/20"
          >
            <div className="flex items-center justify-center pl-3 text-gray-400">
              <Command size={18} />
            </div>

            <input
              ref={inputRef}
              type="text"
              className="flex-1 bg-transparent text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:outline-none py-2 tracking-tight"
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
                className="p-2.5 rounded-xl text-gray-600 hover:text-gray-900 hover:bg-gray-100 cursor-pointer border border-gray-200 flex items-center gap-1.5 text-xs font-semibold shrink-0"
                title="Editar e refazer o último prompt"
              >
                <RotateCcw size={14} />
                <span className="hidden sm:inline tracking-tight">Refazer último</span>
              </button>
            )}

            {isLoading ? (
              <button
                type="button"
                onClick={stopStream}
                className="bg-rose-600 hover:bg-rose-700 text-white font-bold p-3 rounded-xl flex items-center justify-center cursor-pointer shrink-0 animate-pulse"
                title="Pausar / Interromper resposta"
              >
                <Square size={16} fill="currentColor" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-40 text-white font-bold p-3 rounded-xl flex items-center justify-center cursor-pointer shrink-0"
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
