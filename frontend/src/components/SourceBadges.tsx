import React from 'react';
import { ExternalLink, Landmark, ShieldCheck, FileCheck, Globe, FileText } from 'lucide-react';
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

  const validateSafeUrl = (url?: string | null): string | null => {
    if (!url) return null;
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        return parsed.href;
      }
      return null;
    } catch {
      return null;
    }
  };

  const getSourceStyle = (type: string, label: string) => {
    const combined = `${type} ${label}`.toLowerCase();
    if (combined.includes('câmara') || combined.includes('senado') || combined.includes('votação')) {
      return {
        bg: 'bg-sky-50 hover:bg-sky-100/80 text-sky-800 border-sky-200/80',
        icon: <Landmark size={11} className="text-sky-600" />
      };
    }
    if (combined.includes('tse') || combined.includes('bens') || combined.includes('eleição')) {
      return {
        bg: 'bg-emerald-50 hover:bg-emerald-100/80 text-emerald-800 border-emerald-200/80',
        icon: <ShieldCheck size={11} className="text-emerald-600" />
      };
    }
    if (combined.includes('transparência') || combined.includes('cgu') || combined.includes('orçamento')) {
      return {
        bg: 'bg-amber-50 hover:bg-amber-100/80 text-amber-900 border-amber-200/80',
        icon: <FileCheck size={11} className="text-amber-600" />
      };
    }
    if (combined.includes('web') || combined.includes('duck') || combined.includes('lupa') || combined.includes('fato')) {
      return {
        bg: 'bg-purple-50 hover:bg-purple-100/80 text-purple-800 border-purple-200/80',
        icon: <Globe size={11} className="text-purple-600" />
      };
    }
    return {
      bg: 'bg-neutral-100 hover:bg-neutral-200/70 text-neutral-800 border-neutral-200/80',
      icon: <FileText size={11} className="text-neutral-500" />
    };
  };

  return (
    <div className="pt-3 mt-3 border-t border-neutral-100 space-y-2">
      <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">
        Fontes Oficialmente Consultadas ({distinctSources.length}):
      </span>
      <div className="flex flex-wrap gap-1.5 items-center">
        {distinctSources.map((src, sIdx) => {
          const safeUrl = validateSafeUrl(src.url);
          const style = getSourceStyle(src.type, src.label);

          return safeUrl ? (
            <a
              key={sIdx}
              href={safeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-all shadow-2xs cursor-pointer ${style.bg}`}
              title={src.raw_file}
            >
              {style.icon}
              <span>{src.label}</span>
              <ExternalLink size={10} className="opacity-70" />
            </a>
          ) : (
            <span
              key={sIdx}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border shadow-2xs ${style.bg}`}
              title={src.raw_file}
            >
              {style.icon}
              <span>{src.label}</span>
            </span>
          );
        })}
      </div>
    </div>
  );
};
