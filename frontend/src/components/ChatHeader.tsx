import React from 'react';
import { ModelSelector } from './ModelSelector';
import { useChatStore } from '../store/useChatStore';

export const ChatHeader: React.FC = () => {
  const { sessions, activeIdx } = useChatStore();
  const currentSession = sessions[activeIdx];
  const firstUserMsg = currentSession?.messages?.find(m => m.role === 'user');
  const displayLabel = firstUserMsg ? firstUserMsg.content : (currentSession?.label || `Sessão ${activeIdx + 1}`).replace(/\.\.\.$/, '');

  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-neutral-200/80 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 shadow-2xs z-10">
      <div className="flex flex-col gap-0.5 min-w-0">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <h1 className="text-base font-bold text-neutral-900 tracking-tight uppercase">
            Painel de Consulta Legislativa
          </h1>
        </div>
        <p className="text-xs text-neutral-500 truncate max-w-md font-medium">
          {displayLabel}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <ModelSelector />
        
        <div className="hidden sm:inline-flex items-center gap-2 bg-neutral-100 border border-neutral-200/80 text-neutral-700 text-xs font-semibold px-3 py-1.5 rounded-full">
          <span className="text-neutral-500 font-mono text-[10px]">rag-fundamentos</span>
          <span className="inline-flex items-center gap-1 text-emerald-700 font-bold">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            ONLINE
          </span>
        </div>
      </div>
    </header>
  );
};
