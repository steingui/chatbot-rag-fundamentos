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

      <main className="flex-1 flex flex-col h-full bg-[#F2F2F7] overflow-hidden min-w-0">
        <ChatHeader />
        <SuggestionGrid />
        <MessageList />

        <footer className="p-4 sm:p-5 bg-transparent flex flex-col items-center gap-2 shrink-0">
          <form
            onSubmit={handleSubmit}
            className="apple-dock focus-within:border-emerald-500/80 focus-within:ring-4 focus-within:ring-emerald-500/20 rounded-3xl p-2 sm:p-2.5 flex items-center gap-3 w-full max-w-4xl apple-spring"
          >
            <div className="flex items-center justify-center pl-3 text-neutral-500">
              <Command size={18} />
            </div>
            
            <input
              ref={inputRef}
              type="text"
              className="flex-1 bg-transparent text-sm font-semibold text-neutral-950 placeholder:text-neutral-500 focus:outline-none py-2 tracking-tight"
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
                className="p-2.5 rounded-2xl text-neutral-700 hover:text-neutral-950 hover:bg-white/80 apple-spring cursor-pointer border border-black/[0.08] flex items-center gap-1.5 text-xs font-bold shrink-0 active:scale-95 shadow-2xs"
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
                className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold p-3 rounded-2xl apple-spring shadow-md flex items-center justify-center cursor-pointer shrink-0 animate-pulse active:scale-95"
                title="Pausar / Interromper resposta"
              >
                <Square size={16} fill="currentColor" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="bg-gradient-to-tr from-emerald-600 to-emerald-400 hover:brightness-105 disabled:opacity-40 text-neutral-950 font-black p-3 rounded-2xl apple-spring shadow-md flex items-center justify-center cursor-pointer shrink-0 active:scale-95"
                title="Enviar pergunta"
              >
                <Send size={16} className="stroke-[2.5]" />
              </button>
            )}
          </form>
        </footer>
      </main>
    </div>
  );
}
