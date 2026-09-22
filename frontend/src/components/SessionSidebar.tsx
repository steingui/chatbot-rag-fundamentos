import React from 'react';
import { Plus, Clock, Database, Settings, FileText, Eraser, Trash2 } from 'lucide-react';
import { useChatStore, MAX_SESSIONS } from '../store/useChatStore';

const NAV_ITEMS = [
  { icon: Plus, label: 'Novo Chat' },
  { icon: Clock, label: 'Histórico' },
  { icon: Database, label: 'Base de Conhecimento' },
  { icon: Settings, label: 'Configurações' }
] as const;

export const SessionSidebar: React.FC = () => {
  const {
    sessions,
    activeIdx,
    setActiveIdx,
    addSession,
    closeSession,
    clearActiveSession,
    clearAllSessions,
    summarizeConversation,
    isLoading
  } = useChatStore();

  const hasHistory = Boolean(sessions[activeIdx]?.messages?.some(m => m.role === 'user'));

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex h-full w-72 flex-col bg-white border-r border-gray-100 lg:static lg:z-auto shrink-0 select-none">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-6 pt-6 pb-5">
        <div className="relative h-8 w-8 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
          <span className="h-2 w-2 rounded-full bg-white" />
        </div>
        <span className="text-lg font-bold lowercase tracking-tight text-gray-900">rag político</span>
      </div>

      {/* Menu de navegação */}
      <nav className="px-3 space-y-1">
        {NAV_ITEMS.map(({ icon: Icon, label }) => {
          const isNewChat = label === 'Novo Chat';
          const disabled = !isNewChat;

          return (
            <button
              key={label}
              onClick={isNewChat ? addSession : undefined}
              disabled={isNewChat ? sessions.length >= MAX_SESSIONS || isLoading : disabled}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                isNewChat
                  ? 'bg-gray-100 text-gray-900 font-medium cursor-pointer'
                  : 'text-gray-400 font-medium cursor-not-allowed opacity-60'
              }`}
            >
              <Icon size={18} className={isNewChat ? 'text-gray-900' : 'text-gray-400'} />
              <span>{label}</span>
            </button>
          );
        })}
      </nav>

      {/* Sessões recentes */}
      <div className="flex-1 overflow-y-auto px-3 py-4 mt-2 border-t border-gray-100">
        <div className="flex items-center justify-between px-3 pb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
            Sessões ({sessions.length}/{MAX_SESSIONS})
          </span>
        </div>

        <div className="space-y-0.5">
          {sessions.map((sess, idx) => {
            const firstUserMsg = sess.messages?.find(m => m.role === 'user');
            const label = firstUserMsg
              ? firstUserMsg.content
              : (sess.label || `Sessão ${idx + 1}`).replace(/\.\.\.$/, '');
            const isActive = idx === activeIdx;

            return (
              <div
                key={sess.id}
                onClick={() => setActiveIdx(idx)}
                className={`group flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm cursor-pointer transition-colors ${
                  isActive ? 'bg-gray-100 text-gray-900 font-medium' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span className="truncate tracking-tight">{label}</span>

                {sessions.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      closeSession(idx);
                    }}
                    className="opacity-0 group-hover:opacity-100 h-5 w-5 rounded text-gray-400 hover:text-rose-600 flex items-center justify-center cursor-pointer text-xs font-bold shrink-0"
                    title="Fechar sessão"
                  >
                    ×
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Ações de contexto */}
      <div className="px-3 py-3 border-t border-gray-100 space-y-1">
        <button
          onClick={summarizeConversation}
          disabled={isLoading || !hasHistory}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-emerald-800 bg-emerald-50 hover:bg-emerald-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
          title="Resumir o histórico da sessão em 1 tweet (280 caracteres)"
        >
          <FileText size={16} className="shrink-0" />
          <span className="truncate">Resumir chat</span>
        </button>

        <button
          onClick={clearActiveSession}
          disabled={isLoading || !hasHistory}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
          title="Limpar o contexto desta sessão (mantém uma única sessão ativa)"
        >
          <Eraser size={16} className="shrink-0" />
          <span className="truncate">Limpar contexto</span>
        </button>

        <button
          onClick={clearAllSessions}
          disabled={isLoading}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wider text-rose-600 hover:bg-rose-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
          title="Limpar todas as sessões, cookies e dados locais"
        >
          <Trash2 size={14} className="shrink-0" />
          <span className="truncate">Limpar tudo</span>
        </button>
      </div>

      {/* Perfil do usuário */}
      <div className="flex items-center gap-3 px-5 py-4 border-t border-gray-100">
        <div className="h-9 w-9 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-sm shrink-0">
          V
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">Visitante</p>
          <p className="text-xs text-gray-500 truncate">visitante@ragpolitico.app</p>
        </div>
      </div>
    </aside>
  );
};
