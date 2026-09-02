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
    <aside className="w-72 bg-white/95 border-r border-neutral-200/90 p-4 flex flex-col justify-between h-full shrink-0 select-none shadow-sm z-20">
      {/* Brand Header */}
      <div className="flex flex-col gap-3 pb-4 border-b border-neutral-200/80">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-emerald-500 text-neutral-950 flex items-center justify-center font-black shadow-sm">
              <Sparkles size={18} />
            </div>
            <div>
              <h2 className="text-sm font-black text-neutral-900 tracking-tight leading-none">
                RAG Político
              </h2>
              <span className="text-[11px] font-bold text-emerald-700">Transparência Eleitoral</span>
            </div>
          </div>
          <span className="bg-neutral-100 border border-neutral-200 text-neutral-800 text-[10px] font-extrabold px-2 py-0.5 rounded-full">
            v2.0
          </span>
        </div>
      </div>

      {/* Session Section */}
      <div className="flex-1 overflow-y-auto py-4 space-y-3">
        <div className="flex items-center justify-between px-1">
          <span className="text-[11px] font-extrabold text-neutral-500 uppercase tracking-wider">
            Sessões de Chat ({sessions.length}/{MAX_SESSIONS})
          </span>
          <button
            className="h-6 w-6 rounded-lg bg-emerald-500 hover:bg-emerald-600 disabled:opacity-40 text-neutral-950 font-bold flex items-center justify-center transition-all shadow-2xs cursor-pointer"
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
                className={`group relative rounded-xl px-3 py-2.5 text-xs font-bold cursor-pointer transition-all flex items-center justify-between gap-2 border ${
                  isActive
                    ? 'bg-neutral-900 border-neutral-900 text-white shadow-sm'
                    : 'bg-neutral-50/80 border-neutral-200/60 text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className={`h-2 w-2 rounded-full shrink-0 ${isActive ? 'bg-emerald-400' : 'bg-neutral-400'}`} />
                  <span className="truncate">{displayLabel}</span>
                </div>

                {sessions.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      closeSession(idx);
                    }}
                    className={`opacity-0 group-hover:opacity-100 ${
                      isActive ? 'hover:bg-neutral-800 text-neutral-400 hover:text-white' : 'hover:bg-rose-100 text-neutral-400 hover:text-rose-700'
                    } h-5 w-5 rounded-md flex items-center justify-center transition-all cursor-pointer shrink-0 font-bold`}
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
        <div className="bg-neutral-50 border border-neutral-200 rounded-xl p-2 flex items-center justify-between shadow-2xs">
          <span className="text-[10px] font-extrabold text-neutral-600 uppercase px-1">Tamanho Texto</span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={decreaseFontSize}
              disabled={fontSize <= 11}
              className="h-6.5 w-6.5 rounded-lg bg-white border border-neutral-200 hover:bg-neutral-100 disabled:opacity-40 text-neutral-800 flex items-center justify-center transition-all cursor-pointer font-bold"
              title="Diminuir fonte (-)"
            >
              <ZoomOut size={13} />
            </button>
            <span className="text-xs font-mono font-bold text-neutral-900 w-8 text-center">{fontSize}px</span>
            <button
              onClick={increaseFontSize}
              disabled={fontSize >= 20}
              className="h-6.5 w-6.5 rounded-lg bg-white border border-neutral-200 hover:bg-neutral-100 disabled:opacity-40 text-neutral-800 flex items-center justify-center transition-all cursor-pointer font-bold"
              title="Aumentar fonte (+)"
            >
              <ZoomIn size={13} />
            </button>
          </div>
        </div>

        {/* Buttons */}
        <div className="space-y-2">
          <button
            onClick={() => sendMessageStream("Resuma nossa conversa em no máximo 1 tweet (280 caracteres).")}
            disabled={isLoading || !sessions[activeIdx]?.messages.some(m => m.role === 'user')}
            className="w-full bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-200/90 text-emerald-950 font-bold text-xs py-2 px-3 rounded-xl flex items-center gap-2 transition-all shadow-2xs cursor-pointer disabled:opacity-40"
            title="Resumir histórico em 1 tweet (280 caracteres)"
          >
            <FileText size={14} className="text-emerald-700 shrink-0" />
            <span>Resumir Conversa</span>
          </button>

          <button
            onClick={clearActiveSession}
            disabled={isLoading}
            className="w-full bg-white hover:bg-rose-50 border border-neutral-200 hover:border-rose-300 text-rose-700 font-bold text-xs py-2 px-3 rounded-xl flex items-center gap-2 transition-all shadow-2xs cursor-pointer disabled:opacity-40"
            title="Limpar mensagens desta sessão"
          >
            <Trash2 size={14} className="shrink-0" />
            <span>Limpar Sessão</span>
          </button>

          <button
            onClick={clearAllSessions}
            disabled={isLoading}
            className="w-full bg-neutral-100 hover:bg-rose-600 hover:text-white border border-neutral-200 hover:border-rose-600 disabled:opacity-40 text-neutral-700 font-extrabold text-[10px] py-1.5 px-3 rounded-xl flex items-center justify-center gap-1.5 transition-all cursor-pointer uppercase tracking-wider"
            title="Limpar todas as sessões e apagar todos os cookies"
          >
            <Trash2 size={12} className="shrink-0" />
            <span>Limpar Tudo</span>
          </button>
        </div>

        <div className="pt-2 flex items-center gap-2 text-[10px] font-extrabold text-neutral-500">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Câmara · Senado · TSE · CGU</span>
        </div>
      </div>
    </aside>
  );
};
