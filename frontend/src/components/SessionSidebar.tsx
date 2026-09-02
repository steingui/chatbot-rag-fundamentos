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
    <aside className="apple-glass w-72 border-r border-white/60 p-4 flex flex-col justify-between h-full shrink-0 select-none shadow-sm z-20 apple-spring">
      {/* Brand Header */}
      <div className="flex flex-col gap-3 pb-4 border-b border-black/[0.06]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-2xl bg-gradient-to-tr from-emerald-600 to-emerald-400 text-neutral-950 flex items-center justify-center font-black shadow-sm">
              <Sparkles size={18} />
            </div>
            <div>
              <h2 className="text-sm font-black text-neutral-950 tracking-tight leading-none">
                RAG Político
              </h2>
              <span className="text-[11px] font-bold text-emerald-800 tracking-tight">Transparência Eleitoral</span>
            </div>
          </div>
          <span className="bg-white/80 border border-black/[0.08] text-neutral-800 text-[10px] font-extrabold px-2 py-0.5 rounded-full shadow-2xs">
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
            className="h-6 w-6 rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-400 hover:brightness-105 disabled:opacity-40 text-neutral-950 font-bold flex items-center justify-center transition-all shadow-xs cursor-pointer active:scale-95"
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
                className={`group relative rounded-2xl px-3.5 py-2.5 text-xs font-bold cursor-pointer apple-spring flex items-center justify-between gap-2 border ${
                  isActive
                    ? 'apple-glass-dark text-white border-white/10 shadow-md scale-[1.01]'
                    : 'bg-white/50 border-black/[0.05] text-neutral-800 hover:bg-white/90 hover:text-neutral-950 hover:border-black/[0.08]'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className={`h-2 w-2 rounded-full shrink-0 ${isActive ? 'bg-emerald-400 shadow-xs' : 'bg-neutral-400'}`} />
                  <span className="truncate tracking-tight">{displayLabel}</span>
                </div>

                {sessions.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      closeSession(idx);
                    }}
                    className={`opacity-0 group-hover:opacity-100 ${
                      isActive ? 'hover:bg-white/20 text-neutral-400 hover:text-white' : 'hover:bg-rose-100 text-neutral-400 hover:text-rose-700'
                    } h-5 w-5 rounded-lg flex items-center justify-center transition-all cursor-pointer shrink-0 font-bold`}
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
      <div className="pt-3 border-t border-black/[0.06] space-y-2.5">
        {/* Zoom Control */}
        <div className="bg-white/60 border border-black/[0.06] rounded-2xl p-2 flex items-center justify-between shadow-2xs backdrop-blur-md">
          <span className="text-[10px] font-extrabold text-neutral-600 uppercase px-1 tracking-tight">Tamanho Texto</span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={decreaseFontSize}
              disabled={fontSize <= 11}
              className="h-6.5 w-6.5 rounded-xl bg-white border border-black/[0.08] hover:bg-neutral-100 disabled:opacity-40 text-neutral-900 flex items-center justify-center apple-spring cursor-pointer font-bold active:scale-95 shadow-2xs"
              title="Diminuir fonte (-)"
            >
              <ZoomOut size={13} />
            </button>
            <span className="text-xs font-mono font-bold text-neutral-950 w-8 text-center">{fontSize}px</span>
            <button
              onClick={increaseFontSize}
              disabled={fontSize >= 20}
              className="h-6.5 w-6.5 rounded-xl bg-white border border-black/[0.08] hover:bg-neutral-100 disabled:opacity-40 text-neutral-900 flex items-center justify-center apple-spring cursor-pointer font-bold active:scale-95 shadow-2xs"
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
            className="w-full bg-emerald-50/80 hover:bg-emerald-100/90 border border-emerald-200 text-emerald-950 font-bold text-xs py-2.5 px-3.5 rounded-2xl flex items-center gap-2 apple-spring shadow-2xs cursor-pointer disabled:opacity-40 active:scale-[0.98]"
            title="Resumir histórico em 1 tweet (280 caracteres)"
          >
            <FileText size={14} className="text-emerald-700 shrink-0" />
            <span className="tracking-tight">Resumir Conversa</span>
          </button>

          <button
            onClick={clearActiveSession}
            disabled={isLoading}
            className="w-full bg-white/70 hover:bg-rose-50 border border-black/[0.08] hover:border-rose-300 text-rose-700 font-bold text-xs py-2.5 px-3.5 rounded-2xl flex items-center gap-2 apple-spring shadow-2xs cursor-pointer disabled:opacity-40 active:scale-[0.98]"
            title="Limpar mensagens desta sessão"
          >
            <Trash2 size={14} className="shrink-0" />
            <span className="tracking-tight">Limpar Sessão</span>
          </button>

          <button
            onClick={clearAllSessions}
            disabled={isLoading}
            className="w-full bg-neutral-100/80 hover:bg-rose-600 hover:text-white border border-black/[0.08] hover:border-rose-600 disabled:opacity-40 text-neutral-700 font-extrabold text-[10px] py-2 px-3 rounded-2xl flex items-center justify-center gap-1.5 apple-spring cursor-pointer uppercase tracking-wider active:scale-[0.98]"
            title="Limpar todas as sessões e apagar todos os cookies"
          >
            <Trash2 size={12} className="shrink-0" />
            <span>Limpar Tudo</span>
          </button>
        </div>

        <div className="pt-2 flex items-center gap-2 text-[10px] font-extrabold text-neutral-600">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
          <span className="tracking-tight">Câmara · Senado · TSE · CGU</span>
        </div>
      </div>
    </aside>
  );
};
