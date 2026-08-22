import { useState, useEffect } from 'react';
import { X, Database, Zap } from 'lucide-react';
import './IntroModal.css';

export function IntroModal() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    // Only show once per user (can use localStorage)
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
    <div className="modal-overlay">
      <div className="modal-content">
        <button className="modal-close" onClick={handleClose}>
          <X size={20} />
        </button>

        <div className="modal-header">
          <h2 className="modal-title">Inteligência Artificial a favor da Transparência</h2>
        </div>

        <div className="modal-body">
          <div className="modal-section">
            <p>
              Somos um sistema <strong>RAG</strong> <em>(Retrieval-Augmented Generation, ou "Geração Aumentada por Recuperação" — uma técnica que ensina a IA a pesquisar em bibliotecas de arquivos antes de falar)</em> focado em política, legislação e eleições brasileiras, usando fontes oficiais.
            </p>
          </div>

          <div className="modal-section">
            <h3 className="section-subtitle">
              <Database size={16} /> Como funciona?
            </h3>
            <p>
              Através de rotinas de ingestão (pipelines), nossos servidores buscam diariamente os dados do Portal da Transparência (CGU), do Tribunal Superior Eleitoral (TSE), da Câmara dos Deputados e do Senado Federal, convertendo-os em coordenadas matemáticas (embeddings) guardadas em um Banco de Dados Vetorial.
            </p>
            <p>
              No momento da sua pergunta, entra em cena a nossa arquitetura de <strong>Agente (ReAct)</strong>. Ele atua como um maestro: primeiro ele vasculha matematicamente o banco de dados em busca dos documentos oficiais que respondam à sua dúvida. Se julgar necessário, o Agente tem autonomia para executar pesquisas extras na internet em tempo real. Em seguida, ele <strong>mescla o contexto interno do banco com os dados ao vivo da web</strong>, injetando esse super-pacote de informações no cérebro da Inteligência Artificial, obrigando-a a criar um resumo com base exclusiva nesses fatos.
            </p>
          </div>

          <div className="modal-warning">
            <h3 className="warning-title">
              <Zap size={16} /> Aviso Importante
            </h3>
            <p>
              Como toda Inteligência Artificial, o sistema não é perfeito e, por ser um projeto em evolução, operamos atualmente usando modelos LLM em <em>free tier</em> (camada gratuita), que podem ter restrições de raciocínio. O robô pode sofrer alucinações, cometer erros de interpretação, misturar contextos ou fornecer dados imprecisos. Use as respostas apenas como um guia inicial para seus estudos e <strong>sempre confira os links das fontes</strong> citadas ao final de cada resposta.
            </p>
          </div>
        </div>

        <div className="modal-footer">
          <button className="modal-btn-primary" onClick={handleClose}>
            Entendi, começar a explorar
          </button>
        </div>
      </div>
    </div>
  );
}
