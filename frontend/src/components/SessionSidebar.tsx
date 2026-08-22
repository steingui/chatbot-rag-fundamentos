import React from 'react';
import { Terminal, Plus, MessageSquare, Trash2, FileText } from 'lucide-react';
import { useChatStore, MAX_SESSIONS } from '../store/useChatStore';

export const SessionSidebar: React.FC = () => {
  const {
    sessions,
    activeIdx,
    setActiveIdx,
    addSession,
    closeSession,
    clearActiveSession,
    isLoading
  } = useChatStore();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <Terminal size={18} className="brand-icon" />
        <span className="brand-name">rag_politico</span>
        <span className="brand-ver">v1.0</span>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section-header">
          <span>SESSÕES DE CHAT</span>
          <button
            className="icon-btn"
            onClick={addSession}
            disabled={sessions.length >= MAX_SESSIONS || isLoading}
            title="Nova sessão (máx. 5)"
          >
            <Plus size={14} />
          </button>
        </div>

        <div className="session-list">
          {sessions.map((sess, idx) => (
            <div
              key={sess.id}
              className={`session-item ${idx === activeIdx ? 'active' : ''}`}
              onClick={() => setActiveIdx(idx)}
            >
              <MessageSquare size={13} className="session-icon" />
              <span className="session-title">{sess.label}</span>
              {sessions.length > 1 && (
                <button
                  className="close-sess-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    closeSession(idx);
                  }}
                  title="Fechar sessão"
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="sidebar-actions">
        <button
          className="sidebar-btn danger"
          onClick={clearActiveSession}
          disabled={isLoading}
          title="Limpar mensagens desta sessão"
        >
          <Trash2 size={13} />
          <span>Limpar Sessão</span>
        </button>
      </div>

      <div className="sidebar-footer">
        <span className="status-dot"></span>
        <FileText size={11} />
        <span>RAG • Câmara / Senado / TSE</span>
      </div>
    </aside>
  );
};
