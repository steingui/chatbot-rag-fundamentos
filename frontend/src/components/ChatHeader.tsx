import React from 'react';
import { ModelSelector } from './ModelSelector';
import { useChatStore } from '../store/useChatStore';

export const ChatHeader: React.FC = () => {
  const { sessions, activeIdx } = useChatStore();
  const currentSession = sessions[activeIdx];

  return (
    <header className="chat-header">
      <div className="header-info">
        <h1 className="header-title">PAINEL DE CONSULTA LEGISLATIVA</h1>
        <span className="header-sub">
          {currentSession ? currentSession.label : `Sessão ${activeIdx + 1}`}
        </span>
      </div>
      <div className="header-meta">
        <ModelSelector />
        <span className="pinecone-badge">
          PINECONE_INDEX: rag-fundamentos<span className="badge-online">ONLINE</span>
        </span>
      </div>
    </header>
  );
};
