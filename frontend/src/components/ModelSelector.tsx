import React from 'react';
import { Cpu, ChevronDown } from 'lucide-react';
import { useChatStore, FREE_MODELS } from '../store/useChatStore';

export const ModelSelector: React.FC = () => {
  const { selectedModel, setSelectedModel, isLoading } = useChatStore();

  return (
    <div className="relative inline-flex items-center">
      <div className="flex items-center gap-1.5 bg-neutral-100 hover:bg-neutral-200/70 border border-neutral-200/90 rounded-full px-3 py-1.5 text-xs font-semibold text-neutral-800 transition-all cursor-pointer shadow-2xs">
        <Cpu size={13} className="text-neutral-500" />
        <select
          className="bg-transparent text-neutral-800 text-xs font-semibold focus:outline-none cursor-pointer pr-4 appearance-none"
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          disabled={isLoading}
          title="Selecione o modelo LLM do OpenRouter"
        >
          {FREE_MODELS.map((model) => (
            <option key={model.id} value={model.id} className="bg-white text-neutral-900 font-medium py-1">
              {model.label}
            </option>
          ))}
        </select>
        <ChevronDown size={12} className="text-neutral-400 pointer-events-none absolute right-2.5" />
      </div>
    </div>
  );
};
