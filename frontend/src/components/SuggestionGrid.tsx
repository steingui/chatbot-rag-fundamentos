import React from 'react';
import { useChatStore } from '../store/useChatStore';

export const SuggestionGrid: React.FC = () => {
  const { suggestions, sendMessageStream, isLoading } = useChatStore();

  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="suggestions-bar">
      <span className="suggestions-label">SUGESTÕES POPULARES:</span>
      <div className="suggestions-grid">
        {suggestions.slice(0, 4).map((sug, i) => (
          <button
            key={i}
            className="suggestion-card"
            onClick={() => sendMessageStream(sug.prompt)}
            disabled={isLoading}
          >
            <span className="suggestion-text">{sug.prompt}</span>
            <span className="suggestion-count-badge">{sug.count}x</span>
          </button>
        ))}
      </div>
    </div>
  );
};
