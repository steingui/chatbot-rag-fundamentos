import React from 'react';
import { Plus, Trash2, FileText, ZoomIn, ZoomOut, Sparkles } from 'lucide-react';
import { useChatStore, MAX_SESSIONS } from '../store/useChatStore';

export const SessionSidebar: React.FC = () => {
  const {
    sessions,
    activeIdx,
    setActiveIdx,
    addSession,
    closeSession,
    clearActiveSession,
    clearAllSessions,
    fontSize,
    increaseFontSize,
    decreaseFontSize,
    sendMessageStream,
    isLoading
  } = useChatStore();

  return (
    <aside className="w-72 bg-neutral-100/90 border-r border-neutral-200/80 p-4 flex flex-col justify-between h-full shrink-0 select-none shadow-2xs">
      {/* Brand Header */}
      <div className="flex flex-col gap-3 pb-4 border-b border-neutral-200/70">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xl bg-emerald-500 flex items-center justify-center text-neutral-900 font-extrabold shadow-sm">
              <Sparkles size={16} />
            </div>
            <div>
              <h2 className="text-sm font-extrabold text-neutral-900 tracking-tight leading-none">
                RAG Político
              </h2>
              <span className="text-[10px] font-medium text-neutral-500">Transparência Eleitoral</span>
            </div>
          </div>
          <span className="bg-neutral-200/80 text-neutral-700 text-[10px] font-extrabold px-2 py-0.5 rounded-full">
            v2.0
          </span>
        </div>
      </div>

      {/* Session Section */}
      <div className="flex-1 overflow-y-auto py-4 space-y-3">
        <div className="flex items-center justify-between px-1">
          <span className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider">
            Sessões de Chat ({sessions.length}/{MAX_SESSIONS})
          </span>
          <button
            className="h-6 w-6 rounded-lg bg-emerald-500 hover:bg-emerald-600 disabled:opacity-40 text-neutral-900 flex items-center justify-center transition-all shadow-2xs cursor-pointer"
            onClick={addSession}
            disabled={sessions.length >= MAX_SESSIONS || isLoading}
            title="Nova sessão (máx. 5)"
          >
            <Plus size={14} className="stroke-[3]" />
          </button>
        </div>

        <div className="space-y-1.5">
          {sessions.map((sess, idx) => {
            const firstUserMsg = sess.messages?.find(m => m.role === 'user');
            const displayLabel = firstUserMsg ? firstUserMsg.content : (sess.label || `Sessão ${idx + 1}`).replace(/\.\.\.$/, '');
            const isActive = idx === activeIdx;

            return (
              <div
                key={sess.id}
                onClick={() => setActiveIdx(idx)}
                className={`group relative rounded-xl px-3 py-2.5 text-xs font-semibold cursor-pointer transition-all flex items-center justify-between gap-2 border ${
                  isActive
                    ? 'bg-white border-neutral-200/90 text-neutral-900 shadow-sm'
                    : 'bg-transparent border-transparent text-neutral-600 hover:bg-neutral-200/50 hover:text-neutral-900'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`h-2 w-2 rounded-full shrink-0 ${isActive ? 'bg-emerald-500' : 'bg-neutral-300'}`} />
                  <span className="truncate">{displayLabel}</span>
                </div>

                {sessions.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      closeSession(idx);
                    }}
                    className="opacity-0 group-hover:opacity-100 hover:bg-rose-100 text-neutral-400 hover:text-rose-700 h-5 w-5 rounded-md flex items-center justify-center transition-all cursor-pointer shrink-0"
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

      {/* Actions & Zoom Panel */}
      <div className="pt-3 border-t border-neutral-200/80 space-y-2.5">
        {/* Zoom Control */}
        <div className="bg-white/80 border border-neutral-200/80 rounded-xl p-2 flex items-center justify-between shadow-2xs">
          <span className="text-[10px] font-bold text-neutral-500 uppercase px-1">Tamanho Texto</span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={decreaseFontSize}
              disabled={fontSize <= 11}
              className="h-6 w-6 rounded-lg bg-neutral-100 hover:bg-neutral-200 disabled:opacity-40 text-neutral-700 flex items-center justify-center transition-all cursor-pointer"
              title="Diminuir fonte (-)"
            >
              <ZoomOut size={12} />
            </button>
            <span className="text-xs font-mono font-bold text-neutral-800 w-8 text-center">{fontSize}px</span>
            <button
              onClick={increaseFontSize}
              disabled={fontSize >= 20}
              className="h-6 w-6 rounded-lg bg-neutral-100 hover:bg-neutral-200 disabled:opacity-40 text-neutral-700 flex items-center justify-center transition-all cursor-pointer"
              title="Aumentar fonte (+)"
            >
              <ZoomIn size={12} />
            </button>
          </div>
        </div>

        {/* Buttons */}
        <div className="space-y-1.5">
          <button
            onClick={() => sendMessageStream("Resuma nossa conversa em no máximo 1 tweet (280 caracteres).")}
            disabled={isLoading || !sessions[activeIdx]?.messages.some(m => m.role === 'user')}
            className="w-full bg-white hover:bg-neutral-50 disabled:opacity-40 border border-neutral-200/90 text-neutral-800 font-semibold text-xs py-2 px-3 rounded-xl flex items-center gap-2 transition-all shadow-2xs cursor-pointer"
            title="Resumir histórico em 1 tweet (280 caracteres)"
          >
            <FileText size={14} className="text-emerald-600" />
            <span>Resumir Conversa</span>
          </button>

          <button
            onClick={clearActiveSession}
            disabled={isLoading}
            className="w-full bg-white hover:bg-rose-50/70 disabled:opacity-40 border border-neutral-200/90 hover:border-rose-200 text-rose-700 font-semibold text-xs py-2 px-3 rounded-xl flex items-center gap-2 transition-all shadow-2xs cursor-pointer"
            title="Limpar mensagens desta sessão"
          >
            <Trash2 size={14} />
            <span>Limpar Sessão</span>
          </button>

          <button
            onClick={clearAllSessions}
            disabled={isLoading}
            className="w-full bg-neutral-200/70 hover:bg-rose-600 hover:text-white disabled:opacity-40 text-neutral-700 font-bold text-[10px] py-1.5 px-3 rounded-xl flex items-center justify-center gap-1.5 transition-all cursor-pointer uppercase tracking-wider"
            title="Limpar todas as sessões e apagar todos os cookies"
          >
            <Trash2 size={12} />
            <span>Limpar Tudo</span>
          </button>
        </div>

        <div className="pt-2 flex items-center gap-2 text-[10px] font-semibold text-neutral-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          <span>Câmara · Senado · TSE · CGU</span>
        </div>
      </div>
    </aside>
  );
};
