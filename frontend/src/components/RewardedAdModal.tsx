import { useState } from 'react';
import { PlayCircle, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';
import { showRewardedAd, resolveAdProvider } from '../lib/rewardedAds';

// MON-603: Modal "Assistir Vídeo para Continuar" com contador transparente e fallback.
export function RewardedAdModal() {
  const { adLocked, guestPromptCount, unlockRewardedAd } = useChatStore();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [grace, setGrace] = useState(false);

  if (!adLocked) return null;

  const handleWatch = async () => {
    setBusy(true);
    setError(null);
    const result = await showRewardedAd();
    setBusy(false);

    if (result.completed) {
      unlockRewardedAd();
      setGrace(false);
      return;
    }

    // MON-605: fallback gracioso (Free Grace) quando não há anúncio disponível.
    if (resolveAdProvider(import.meta.env?.VITE_ADS_MODE) === 'unavailable') {
      setGrace(true);
      unlockRewardedAd();
      return;
    }

    setError(
      result.provider === 'mock'
        ? 'Sem anúncio disponível agora. Tente novamente em instantes.'
        : 'O anúncio não pôde ser carregado. Você não perdeu prompts.'
    );
  };

  return (
    <div className="fixed inset-0 z-50 bg-neutral-950/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl border border-neutral-200 shadow-2xl max-w-md w-full p-6 sm:p-8 space-y-5 text-center">
        <div className="mx-auto h-12 w-12 rounded-2xl bg-emerald-500 text-neutral-900 flex items-center justify-center shadow-md">
          <PlayCircle size={24} />
        </div>

        <div className="space-y-1.5">
          <h2 className="text-xl font-extrabold text-neutral-900 tracking-tight">
            Assistir Vídeo para Continuar
          </h2>
          <p className="text-sm text-neutral-600 font-medium">
            Você usou <strong className="text-neutral-900">{guestPromptCount}</strong> prompts.
            Assista 1 anúncio para liberar o próximo lote de 3.
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-left">
            <AlertTriangle size={16} className="text-amber-600 shrink-0" />
            <p className="text-xs font-semibold text-amber-800">{error}</p>
          </div>
        )}

        {grace && (
          <div className="flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-left">
            <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
            <p className="text-xs font-semibold text-emerald-800">
              Anúncio indisponível na sua região — liberamos o próximo lote gratuitamente.
            </p>
          </div>
        )}

        <button
          type="button"
          onClick={handleWatch}
          disabled={busy}
          className="w-full bg-gradient-to-tr from-emerald-600 to-emerald-400 hover:brightness-105 disabled:opacity-50 text-neutral-950 font-black py-3 rounded-2xl apple-spring shadow-md cursor-pointer active:scale-95"
        >
          {busy ? 'Carregando anúncio…' : 'Assistir Vídeo e Continuar'}
        </button>

        <p className="text-[11px] text-neutral-400 font-medium leading-relaxed">
          Anúncios mantêm a plataforma gratuita. Seu progresso e histórico não são alterados.
        </p>
      </div>
    </div>
  );
}
