import React from 'react';
import { FileUp, KeyRound } from 'lucide-react';

const SETUP_ITEMS = [
  {
    icon: FileUp,
    title: 'Fazer upload de documentos',
    subtitle: 'Enriqueça a base de conhecimento com seus arquivos'
  },
  {
    icon: KeyRound,
    title: 'Configurar API Key do LLM',
    subtitle: 'Conecte seu próprio provedor de IA para gerar respostas'
  }
] as const;

export const DashboardCards: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <h3 className="font-bold text-gray-900">Chats Recentes</h3>
          <p className="text-sm text-gray-500 mt-1">Você ainda não fez uma consulta.</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <h3 className="font-bold text-gray-900">Próximos Passos</h3>
          <p className="text-sm text-gray-500 mt-1">Suas sugestões de consulta aparecerão aqui.</p>
        </div>
      </div>

      <section className="bg-white rounded-xl shadow-sm border border-gray-200">
        <h3 className="px-6 pt-6 text-base font-bold text-gray-900">Terminar a configuração</h3>

        <div className="mt-4">
          {SETUP_ITEMS.map((item, i) => (
            <React.Fragment key={item.title}>
              {i > 0 && <div className="mx-6 border-t border-gray-100" />}
              <div className="flex items-center gap-4 px-6 py-5">
                <div className="h-10 w-10 rounded-lg border border-gray-200 flex items-center justify-center text-gray-700 shrink-0">
                  <item.icon size={18} />
                </div>

                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-semibold text-gray-900">{item.title}</h4>
                  <p className="text-sm text-gray-500">{item.subtitle}</p>
                </div>

                <div className="h-6 w-6 rounded-full border-2 border-dashed border-gray-300 shrink-0" />
              </div>
            </React.Fragment>
          ))}
        </div>
      </section>
    </div>
  );
};
