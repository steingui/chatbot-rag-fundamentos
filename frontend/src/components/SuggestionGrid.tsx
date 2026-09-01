import React from 'react';
import { Sparkles } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const SuggestionGrid: React.FC = () => {
  const { suggestions, showSuggestions, sendMessageStream, isLoading } = useChatStore();

  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div
      className={`px-4 sm:px-6 py-2.5 bg-neutral-100/60 border-b border-neutral-200/60 flex flex-wrap items-center gap-2.5 transition-all duration-300 ${
        showSuggestions ? 'opacity-100' : 'opacity-0 max-h-0 overflow-hidden py-0 border-none'
      }`}
    >
      <div className="flex items-center gap-1.5 shrink-0 text-neutral-400">
        <Sparkles size={13} className="text-emerald-500" />
        <span className="text-[10px] font-bold uppercase tracking-wider">Sugestões:</span>
      </div>

      <div className="flex flex-wrap items-center gap-2 flex-1">
        {suggestions.slice(0, 4).map((sug, i) => (
          <button
            key={i}
            onClick={() => sendMessageStream(sug.prompt)}
            disabled={isLoading}
            className="rounded-full bg-white hover:bg-neutral-900 hover:text-white border border-neutral-200/90 text-neutral-700 text-xs px-3.5 py-1 font-semibold transition-all shadow-2xs disabled:opacity-40 cursor-pointer text-left"
          >
            {sug.prompt}
          </button>
        ))}
      </div>
    </div>
  );
};
