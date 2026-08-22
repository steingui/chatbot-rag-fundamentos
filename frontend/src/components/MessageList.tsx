import React, { useRef, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Loader2 } from 'lucide-react';
import { useChatStore, formatMarkdown, formatTime } from '../store/useChatStore';
import { SourceBadges } from './SourceBadges';

export const MessageList: React.FC = () => {
  const { sessions, activeIdx, isLoading, selectedModel } = useChatStore();
  const currentSession = sessions[activeIdx];
  const messages = currentSession?.messages || [];

  const getBotAuthorLabel = (modelId: string) => {
    if (!modelId) return 'llm@rag_eleicoes';
    if (modelId.includes('deepseek')) return 'deepseek_r1@rag_eleicoes';
    if (modelId.includes('nemotron')) return 'nemotron_30b@rag_eleicoes';
    if (modelId.includes('llama')) return 'llama_70b@rag_eleicoes';
    if (modelId.includes('gemini')) return 'gemini_flash@rag_eleicoes';
    if (modelId.includes('qwen')) return 'qwen_72b@rag_eleicoes';
    
    const name = modelId.split('/')[1] || modelId.split('/')[0] || 'llm';
    const clean = name.split(':')[0].replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
    return `${clean}@rag_eleicoes`;
  };

  const parentRef = useRef<HTMLDivElement>(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = React.useState(true);
  const prevMessagesLength = useRef(messages.length);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // estimativa em pixels por mensagem
    overscan: 5
  });

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    const isBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 100;
    setIsAutoScrollEnabled(isBottom);
  };

  // Auto-scroll condicional: sempre rola em nova mensagem, ou se o usuário estiver no fim
  useEffect(() => {
    const isNewMessage = messages.length > prevMessagesLength.current;
    prevMessagesLength.current = messages.length;

    if (messages.length > 0) {
      if (isNewMessage || isAutoScrollEnabled) {
        virtualizer.scrollToIndex(messages.length - 1, { align: 'end' });
      }
    }
  }, [messages.length, messages[messages.length - 1]?.content, virtualizer, isAutoScrollEnabled]);

  return (
    <div className="messages-area" ref={parentRef} onScroll={handleScroll}>
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative'
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const msg = messages[virtualItem.index];
          if (!msg) return null;

          return (
            <div
              key={msg.id}
              ref={virtualizer.measureElement}
              data-index={virtualItem.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`
              }}
              className={`message-wrapper ${msg.role}`}
            >
              <div className={`message-bubble ${msg.role}`}>
                <div className="msg-header">
                  {msg.role === 'user' ? (
                    <span className="msg-author user-author">
                      you@{currentSession?.id ? currentSession.id.replace(/^session-/, '').slice(0, 8) : 'usr'}:~$
                    </span>
                  ) : (
                    <div className="bot-header-title">
                      <span className="bot-bolt">⚡</span>
                      <span className="bot-author">{getBotAuthorLabel(selectedModel)}</span>
                    </div>
                  )}
                  <span className="msg-time">{formatTime(new Date(msg.timestamp))}</span>
                </div>

                {msg.role === 'bot' && !msg.content && isLoading ? (
                  <div className="typing-indicator">
                    <Loader2 size={14} className="spin-icon" />
                    <span>Gerando síntese legislativa...</span>
                  </div>
                ) : (
                  <div
                    className="msg-content bot-text"
                    dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                  />
                )}

                {msg.role === 'bot' && <SourceBadges sources={msg.sources} />}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
