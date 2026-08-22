import React from 'react';
import { Cpu } from 'lucide-react';
import { useChatStore, FREE_MODELS } from '../store/useChatStore';

export const ModelSelector: React.FC = () => {
  const { selectedModel, setSelectedModel, isLoading } = useChatStore();

  return (
    <div className="model-selector-wrapper">
      <Cpu size={12} className="model-icon" />
      <select
        className="model-select"
        value={selectedModel}
        onChange={(e) => setSelectedModel(e.target.value)}
        disabled={isLoading}
        title="Selecione o modelo LLM do OpenRouter"
      >
        {FREE_MODELS.map((model) => (
          <option key={model.id} value={model.id}>
            {model.label}
          </option>
        ))}
      </select>
    </div>
  );
};
