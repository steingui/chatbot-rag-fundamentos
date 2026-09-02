import React from 'react';
import { Sparkles } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';

export const SuggestionGrid: React.FC = () => {
  const { suggestions, showSuggestions, sendMessageStream, isLoading } = useChatStore();

  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div
      className={`px-4 sm:px-6 py-2.5 bg-white/40 border-b border-black/[0.05] flex flex-wrap items-center gap-2.5 backdrop-blur-md apple-spring ${
        showSuggestions ? 'opacity-100' : 'opacity-0 max-h-0 overflow-hidden py-0 border-none'
      }`}
    >
      <div className="flex items-center gap-1.5 shrink-0 text-neutral-700">
        <Sparkles size={14} className="text-emerald-600 shrink-0" />
        <span className="text-[11px] font-extrabold uppercase tracking-wider text-neutral-600">Sugestões Rápidas:</span>
      </div>

      <div className="flex flex-wrap items-center gap-2 flex-1">
        {suggestions.slice(0, 4).map((sug, i) => (
          <button
            key={i}
            onClick={() => sendMessageStream(sug.prompt)}
            disabled={isLoading}
            className="rounded-full bg-white/80 hover:bg-neutral-950 hover:text-white border border-black/[0.08] hover:border-neutral-950 text-neutral-900 text-xs px-3.5 py-1.5 font-bold apple-spring shadow-2xs backdrop-blur-md disabled:opacity-40 cursor-pointer text-left hover:scale-[1.02] active:scale-[0.98] tracking-tight"
          >
            {sug.prompt}
          </button>
        ))}
      </div>
    </div>
  );
};
