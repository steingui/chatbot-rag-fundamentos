import React from 'react';
import { useChatStore } from '../store/useChatStore';

export const SuggestionGrid: React.FC = () => {
  const { suggestions, sendMessageStream, isLoading } = useChatStore();

  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="suggestions-container">
      <span className="suggestions-header-label">SUGESTÕES POPULARES:</span>
      <div className="suggestions-horizontal-grid">
        {suggestions.slice(0, 8).map((sug, i) => (
          <button
            key={i}
            className="suggestion-card-item"
            onClick={() => sendMessageStream(sug.prompt)}
            disabled={isLoading}
          >
            <span className="suggestion-card-text">{sug.prompt}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
