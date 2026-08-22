import React, { useRef, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Loader2 } from 'lucide-react';
import { useChatStore, formatMarkdown, formatTime } from '../store/useChatStore';
import { SourceBadges } from './SourceBadges';

export const MessageList: React.FC = () => {
  const { sessions, activeIdx, isLoading } = useChatStore();
  const currentSession = sessions[activeIdx];
  const messages = currentSession?.messages || [];

  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // estimativa em pixels por mensagem
    overscan: 5
  });

  // Auto-scroll para o final quando uma nova mensagem/token chega
  useEffect(() => {
    if (messages.length > 0) {
      virtualizer.scrollToIndex(messages.length - 1, { align: 'end' });
    }
  }, [messages.length, messages[messages.length - 1]?.content, virtualizer]);

  return (
    <div className="messages-area" ref={parentRef}>
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
                      <span className="bot-author">CIVIC_AI</span>
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
