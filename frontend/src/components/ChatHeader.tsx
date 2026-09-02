import React from 'react';
import { PanelLeft, PanelLeftClose } from 'lucide-react';
import { ModelSelector } from './ModelSelector';
import { useChatStore } from '../store/useChatStore';

export const ChatHeader: React.FC = () => {
  const { sessions, activeIdx, isSidebarOpen, toggleSidebar } = useChatStore();
  const currentSession = sessions[activeIdx];
  const firstUserMsg = currentSession?.messages?.find(m => m.role === 'user');
  const displayLabel = firstUserMsg ? firstUserMsg.content : (currentSession?.label || `Sessão ${activeIdx + 1}`).replace(/\.\.\.$/, '');

  return (
    <header className="apple-glass h-16 border-b border-white/60 px-4 sm:px-6 flex items-center justify-between gap-4 shadow-2xs z-10 shrink-0 apple-spring">
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-2xl text-neutral-700 hover:text-neutral-950 hover:bg-white/80 apple-spring cursor-pointer border border-black/[0.08] shadow-2xs active:scale-95"
          title={isSidebarOpen ? 'Recolher menu lateral' : 'Expandir menu lateral'}
        >
          {isSidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeft size={18} />}
        </button>

        <div className="flex flex-col gap-0.5 min-w-0">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse shrink-0 shadow-xs" />
            <h1 className="text-sm sm:text-base font-black text-neutral-950 tracking-tight uppercase">
              PAINEL DE CONSULTA LEGISLATIVA
            </h1>
          </div>
          <p className="text-xs text-neutral-600 font-semibold max-w-3xl leading-snug break-words tracking-tight">
            {displayLabel}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <ModelSelector />
        
        <div className="hidden sm:inline-flex items-center gap-2 bg-white/80 border border-black/[0.08] text-neutral-800 text-xs font-extrabold px-3 py-1.5 rounded-full shadow-2xs backdrop-blur-md">
          <span className="text-neutral-500 font-mono text-[11px]">rag-fundamentos</span>
          <span className="inline-flex items-center gap-1.5 text-emerald-800 font-black">
            <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-2xs" />
            ONLINE
          </span>
        </div>
      </div>
    </header>
  );
};
