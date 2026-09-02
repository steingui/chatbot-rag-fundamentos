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
        bg: 'bg-white/80 hover:bg-emerald-50/90 text-neutral-900 hover:text-emerald-950 border-black/[0.08] hover:border-emerald-300',
        icon: <Landmark size={12} className="text-emerald-600 shrink-0" />
      };
    }
    if (combined.includes('tse') || combined.includes('bens') || combined.includes('eleição')) {
      return {
        bg: 'bg-white/80 hover:bg-emerald-50/90 text-neutral-900 hover:text-emerald-950 border-black/[0.08] hover:border-emerald-300',
        icon: <ShieldCheck size={12} className="text-emerald-600 shrink-0" />
      };
    }
    if (combined.includes('transparência') || combined.includes('cgu') || combined.includes('orçamento')) {
      return {
        bg: 'bg-white/80 hover:bg-emerald-50/90 text-neutral-900 hover:text-emerald-950 border-black/[0.08] hover:border-emerald-300',
        icon: <FileCheck size={12} className="text-emerald-600 shrink-0" />
      };
    }
    if (combined.includes('web') || combined.includes('duck') || combined.includes('lupa') || combined.includes('fato')) {
      return {
        bg: 'bg-white/80 hover:bg-emerald-50/90 text-neutral-900 hover:text-emerald-950 border-black/[0.08] hover:border-emerald-300',
        icon: <Globe size={12} className="text-emerald-600 shrink-0" />
      };
    }
    return {
      bg: 'bg-white/80 hover:bg-emerald-50/90 text-neutral-900 hover:text-emerald-950 border-black/[0.08] hover:border-emerald-300',
      icon: <FileText size={12} className="text-neutral-600 shrink-0" />
    };
  };

  return (
    <div className="pt-3 mt-3 border-t border-black/[0.06] space-y-2">
      <div className="flex items-center gap-1.5">
        <span className="text-[11px] font-extrabold text-neutral-500 uppercase tracking-wider">
          Fontes Oficialmente Consultadas
        </span>
        <span className="bg-emerald-100/80 text-emerald-950 text-[10px] font-extrabold px-2 py-0.5 rounded-full border border-emerald-200">
          {distinctSources.length}
        </span>
      </div>
      <div className="flex flex-wrap gap-2 items-center">
        {distinctSources.map((src, sIdx) => {
          const safeUrl = validateSafeUrl(src.url);
          const style = getSourceStyle(src.type, src.label);

          return safeUrl ? (
            <a
              key={sIdx}
              href={safeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border apple-spring shadow-2xs backdrop-blur-md cursor-pointer hover:scale-[1.02] active:scale-[0.98] ${style.bg}`}
              title={src.raw_file}
            >
              {style.icon}
              <span className="tracking-tight">{src.label}</span>
              <ExternalLink size={10} className="opacity-70 shrink-0" />
            </a>
          ) : (
            <span
              key={sIdx}
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border shadow-2xs backdrop-blur-md ${style.bg}`}
              title={src.raw_file}
            >
              {style.icon}
              <span className="tracking-tight">{src.label}</span>
            </span>
          );
        })}
      </div>
    </div>
  );
};
