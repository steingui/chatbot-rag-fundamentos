import { useEffect, useRef } from 'react';
import { Send, Loader2, Command } from 'lucide-react';
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
    <div className="flex h-screen w-screen bg-[#F4F4F6] text-neutral-900 font-sans overflow-hidden">
      <IntroModal />
      <SessionSidebar />

      <main className="flex-1 flex flex-col h-full bg-[#F4F4F6] overflow-hidden min-w-0">
        <ChatHeader />
        <SuggestionGrid />
        <MessageList />

        <footer className="p-4 bg-[#F4F4F6] border-t border-neutral-200/60 flex justify-center shrink-0">
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

            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-40 text-neutral-900 font-bold p-3 rounded-xl transition-all shadow-sm flex items-center justify-center cursor-pointer shrink-0"
              title="Enviar pergunta"
            >
              {isLoading ? (
                <Loader2 size={16} className="animate-spin text-neutral-900" />
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
