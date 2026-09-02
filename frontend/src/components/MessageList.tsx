import React, { useRef, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Loader2, User, Sparkles } from 'lucide-react';
import { useChatStore, formatMarkdown, formatTime } from '../store/useChatStore';
import { SourceBadges } from './SourceBadges';

export const MessageList: React.FC = () => {
  const { sessions, activeIdx, isLoading, selectedModel, setShowSuggestions } = useChatStore();
  const currentSession = sessions[activeIdx];
  const messages = currentSession?.messages || [];

  const getBotAuthorLabel = (modelId: string) => {
    if (!modelId) return 'RAG Assistant';
    if (modelId.includes('deepseek')) return 'DeepSeek R1';
    if (modelId.includes('nemotron')) return 'Nemotron 3.5';
    if (modelId.includes('llama')) return 'Llama 3.3 70B';
    if (modelId.includes('gemini')) return 'Gemini 3.7 Flash';
    if (modelId.includes('gemma')) return 'Gemma 4 31B';
    
    const name = modelId.split('/')[1] || modelId.split('/')[0] || 'LLM';
    return name.split(':')[0].replace(/[-_]/g, ' ');
  };

  const parentRef = useRef<HTMLDivElement>(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = React.useState(true);
  const prevMessagesLength = useRef(messages.length);
  const prevScrollInfo = useRef({ scrollTop: 0, scrollHeight: 0, clientHeight: 0 });

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 140,
    overscan: 5
  });

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    const isBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 100;
    setIsAutoScrollEnabled(isBottom);
    
    const prev = prevScrollInfo.current;
    if (scrollHeight === prev.scrollHeight) {
      const prevDistanceFromBottom = prev.scrollHeight - prev.clientHeight - prev.scrollTop;
      const currentDistanceFromBottom = scrollHeight - clientHeight - scrollTop;
      
      if (currentDistanceFromBottom < prevDistanceFromBottom - 5) {
        setShowSuggestions(false);
      } else if (currentDistanceFromBottom > prevDistanceFromBottom + 5) {
        setShowSuggestions(true);
      }
    }
    
    prevScrollInfo.current = { scrollTop, scrollHeight, clientHeight };
  };

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
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4" ref={parentRef} onScroll={handleScroll}>
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
          const isUser = msg.role === 'user';

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
              className={`pb-4 flex ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {isUser ? (
                /* User Card - Sleek High-Contrast Dark Card */
                <div className="bg-neutral-900 text-white border border-neutral-800 rounded-2xl rounded-tr-xs p-4 shadow-md max-w-2xl w-full space-y-2.5">
                  <div className="flex items-center justify-between border-b border-neutral-800/80 pb-2">
                    <div className="flex items-center gap-2">
                      <div className="h-6 w-6 rounded-full bg-emerald-500 text-neutral-950 font-black text-xs flex items-center justify-center shadow-2xs">
                        <User size={13} />
                      </div>
                      <span className="text-xs font-bold text-emerald-400 tracking-wide uppercase">Você</span>
                    </div>
                    <span className="text-[11px] font-mono text-neutral-400">{formatTime(new Date(msg.timestamp))}</span>
                  </div>
                  <div className="text-sm font-medium text-neutral-100 leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </div>
                </div>
              ) : (
                /* Bot Card - Clean Modern High-Contrast Light Card */
                <div className="bg-white text-neutral-900 border border-neutral-200/90 rounded-2xl rounded-tl-xs p-5 shadow-sm max-w-3xl w-full space-y-3.5">
                  <div className="flex items-center justify-between border-b border-neutral-100 pb-2.5">
                    <div className="flex items-center gap-2.5">
                      <div className="h-7 w-7 rounded-xl bg-emerald-500 text-neutral-950 font-black text-xs flex items-center justify-center shadow-2xs">
                        <Sparkles size={15} />
                      </div>
                      <div>
                        <span className="text-xs font-extrabold text-neutral-900 block leading-tight">
                          {getBotAuthorLabel(selectedModel)}
                        </span>
                        <span className="text-[11px] text-neutral-500 font-semibold">Resposta Baseada em Dados Oficiais</span>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono text-neutral-500 font-medium">{formatTime(new Date(msg.timestamp))}</span>
                  </div>

                  {!msg.content && isLoading ? (
                    <div className="flex items-center gap-2.5 text-xs font-bold text-neutral-600 py-3">
                      <Loader2 size={16} className="animate-spin text-emerald-600" />
                      <span>Consultando bases legislativas e gerando resposta...</span>
                    </div>
                  ) : (
                    <div
                      className="prose prose-neutral max-w-none text-sm text-neutral-800 leading-relaxed font-normal space-y-2.5 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:mb-2.5 [&_h3]:font-bold [&_h3]:text-base [&_h3]:text-neutral-900 [&_code]:bg-neutral-100 [&_code]:text-emerald-800 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded-md [&_code]:text-xs [&_code]:font-mono [&_code]:font-semibold"
                      dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                    />
                  )}

                  <SourceBadges sources={msg.sources} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
