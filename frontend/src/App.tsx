import { useState, useRef, useEffect } from 'react';
import { Send, Bot, Link as LinkIcon } from 'lucide-react';
import './App.css';

type Source = {
  type: string;
  label: string;
  url?: string;
  raw_file: string;
};

type Message = {
  id: string;
  type: 'user' | 'bot';
  content: string;
  sources?: Source[];
};

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: 'Olá! Sou seu assistente de dados Políticos. O que você gostaria de saber sobre projetos de lei, propostas de governo ou checagem de fatos?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Um session_id fixo por aba para manter a memória do Langchain
  const sessionId = useRef(`session-${Math.random().toString(36).substring(7)}`);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Bate na API de produção ou localhost
      const apiUrl = 'https://chatbot-rag-api-q2k5.onrender.com/chat';
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId.current,
          query: userMessage.content
        })
      });

      if (!response.ok) {
        throw new Error('Falha ao obter resposta da API');
      }

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: data.answer,
        sources: data.sources
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error(error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: 'Desculpe, ocorreu um erro ao consultar a base de dados. Tente novamente em instantes.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <Bot size={32} color="var(--accent-color)" />
        <div>
          <h1>RAG Político</h1>
          <p>Conectado à Câmara, TSE e Fato ou Fake</p>
        </div>
      </header>

      <main className="messages-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.type}`}>
            <div className="message-bubble">
              {msg.type === 'user' ? (
                msg.content
              ) : (
                <div dangerouslySetInnerHTML={{ __html: msg.content.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
              )}
            </div>
            
            {msg.sources && msg.sources.length > 0 && (
              <div className="sources-container">
                {msg.sources.map((source, idx) => (
                  source.url ? (
                    <a key={idx} href={source.url} target="_blank" rel="noopener noreferrer" className="source-tag" title={source.raw_file}>
                      <LinkIcon size={12} />
                      {source.label}
                    </a>
                  ) : (
                    <span key={idx} className="source-tag" title={source.raw_file}>
                      {source.label}
                    </span>
                  )
                ))}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="message-wrapper bot">
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Pergunte sobre pautas, financiamentos ou fact-checking..."
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={!input.trim() || isLoading}>
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
