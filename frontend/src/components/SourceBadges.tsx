import React from 'react';
import { ExternalLink } from 'lucide-react';
import { Source } from '../store/useChatStore';

interface SourceBadgesProps {
  sources?: Source[];
}

export const SourceBadges: React.FC<SourceBadgesProps> = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  const seenKeys = new Set<string>();
  const distinctSources = sources.filter(src => {
    const key = `${src.label}||${src.url || ''}`;
    if (seenKeys.has(key)) return false;
    seenKeys.add(key);
    return true;
  });

  return (
    <div className="msg-sources">
      <div className="sources-row">
        <span className="sources-label">FONTES CONSULTADAS:</span>
        {distinctSources.map((src, sIdx) => (
          src.url ? (
            <a
              key={sIdx}
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              className="source-chip"
              title={src.raw_file}
            >
              <span>{src.label}</span>
              <ExternalLink size={10} />
            </a>
          ) : (
            <span key={sIdx} className="source-chip no-link" title={src.raw_file}>
              {src.label}
            </span>
          )
        ))}
      </div>
    </div>
  );
};
