import { useState, useEffect } from 'react';
import { X, Database, Zap, Sparkles } from 'lucide-react';

export function IntroModal() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const hasSeenIntro = localStorage.getItem('hasSeenIntro');
    if (!hasSeenIntro) {
      setIsOpen(true);
    }
  }, []);

  const handleClose = () => {
    setIsOpen(false);
    localStorage.setItem('hasSeenIntro', 'true');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-neutral-950/40 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl border border-neutral-200 shadow-2xl max-w-2xl w-full p-6 sm:p-8 relative space-y-6 max-h-[90vh] overflow-y-auto">
        <button
          onClick={handleClose}
          className="absolute top-5 right-5 text-neutral-400 hover:text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded-full h-8 w-8 flex items-center justify-center transition-all cursor-pointer"
          title="Fechar"
        >
          <X size={18} />
        </button>

        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-emerald-500 text-neutral-900 font-extrabold flex items-center justify-center shadow-md">
            <Sparkles size={20} />
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-neutral-900 tracking-tight">
              Inteligência Artificial & Transparência
            </h2>
            <p className="text-xs text-neutral-500 font-medium">Plataforma de Consulta RAG em Dados Públicos</p>
          </div>
        </div>

        <div className="space-y-4 text-sm text-neutral-700 leading-relaxed font-normal">
          <p className="bg-neutral-50 p-4 rounded-2xl border border-neutral-200/80">
            Somos um sistema <strong>RAG</strong> <em>(Retrieval-Augmented Generation)</em> focado em política e legislação brasileira, consultando bases oficiais em tempo real para gerar análises sem alucinações.
          </p>

          <div className="space-y-2">
            <h3 className="font-bold text-neutral-900 flex items-center gap-2 text-sm">
              <Database size={16} className="text-emerald-600" /> Como Funciona a Busca?
            </h3>
            <p className="text-xs text-neutral-600 leading-relaxed">
              Nossos servidores sincronizam diariamente dados da Câmara dos Deputados, Senado Federal, Tribunal Superior Eleitoral (TSE) e Portal da Transparência (CGU).
              O Agente (ReAct) analisa sua pergunta, recupera documentos vetoriais e executa checagens web complementares antes de construir a resposta final.
            </p>
          </div>

          <div className="bg-rose-50/70 border border-rose-200/80 p-4 rounded-2xl space-y-1.5">
            <h3 className="font-bold text-rose-900 flex items-center gap-2 text-xs uppercase tracking-wider">
              <Zap size={14} className="text-rose-600" /> Transparência & Limitações
            </h3>
            <p className="text-xs text-rose-800 leading-relaxed">
              O sistema utiliza modelos em camada gratuita (Free Tier). Respostas devem ser usadas como guia inicial. <strong>Sempre valide as fontes citadas nos links do assistente.</strong>
            </p>
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={handleClose}
            className="w-full sm:w-auto bg-emerald-500 hover:bg-emerald-600 text-neutral-900 font-bold px-6 py-3 rounded-2xl transition-all shadow-md cursor-pointer"
          >
            Entendi, começar a explorar
          </button>
        </div>
      </div>
    </div>
  );
}
