import React from 'react';
import { Cpu, ChevronDown } from 'lucide-react';
import { useChatStore, FREE_MODELS } from '../store/useChatStore';

export const ModelSelector: React.FC = () => {
  const { selectedModel, setSelectedModel, isLoading } = useChatStore();

  return (
    <div className="relative inline-flex items-center">
      <div className="flex items-center gap-1.5 bg-white/80 hover:bg-white border border-black/[0.08] hover:border-black/20 rounded-full px-3.5 py-1.5 text-xs font-bold text-neutral-950 apple-spring cursor-pointer shadow-2xs backdrop-blur-md hover:scale-[1.01] active:scale-[0.98]">
        <Cpu size={14} className="text-emerald-600 shrink-0" />
        <select
          className="bg-transparent text-neutral-950 text-xs font-extrabold focus:outline-none cursor-pointer pr-4 appearance-none tracking-tight"
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          disabled={isLoading}
          title="Selecione o modelo LLM do OpenRouter"
        >
          {FREE_MODELS.map((model) => (
            <option key={model.id} value={model.id} className="bg-white text-neutral-950 font-semibold py-1">
              {model.label}
            </option>
          ))}
        </select>
        <ChevronDown size={13} className="text-neutral-500 pointer-events-none absolute right-3" />
      </div>
    </div>
  );
};
