import React from 'react';
import { Menu, X } from 'lucide-react';
import { ModelSelector } from './ModelSelector';
import { useChatStore } from '../store/useChatStore';

export const ChatHeader: React.FC = () => {
  const { isSidebarOpen, toggleSidebar } = useChatStore();

  return (
    <header className="flex items-center justify-between gap-4 px-4 sm:px-6 lg:px-8 py-5 shrink-0">
      <div className="flex items-center gap-4 min-w-0">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 cursor-pointer shrink-0"
          title={isSidebarOpen ? 'Recolher menu' : 'Abrir menu'}
        >
          {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Olá, Visitante</h1>
          <p className="text-sm text-gray-500">Boas-vindas à RAG Político</p>
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <ModelSelector />
      </div>
    </header>
  );
};
