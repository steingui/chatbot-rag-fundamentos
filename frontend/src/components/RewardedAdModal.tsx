import { useState } from 'react';
import { PlayCircle, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';
import { showRewardedAd, resolveAdProvider } from '../lib/rewardedAds';

// MON-603: modal de desbloqueio via Rewarded Ad, exibido somente quando o
// contador trava o lote (adLocked). Banner de antecipação removido (paywall
// de "1 prompt restante" desativado temporariamente).
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
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6">
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 space-y-3 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-emerald-500 text-neutral-900 flex items-center justify-center shadow-md shrink-0">
            <PlayCircle size={20} />
          </div>
          <div className="space-y-0.5">
            <h2 className="text-sm font-extrabold text-neutral-900 tracking-tight">
              Assistir Vídeo para Continuar
            </h2>
            <p className="text-xs text-neutral-600 font-medium">
              Você usou <strong className="text-neutral-900">{guestPromptCount}</strong> prompts.
              Assista 1 anúncio para liberar o próximo lote de 3.
            </p>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-white/70 p-2.5 text-left">
            <AlertTriangle size={14} className="text-amber-600 shrink-0" />
            <p className="text-xs font-semibold text-amber-800">{error}</p>
          </div>
        )}

        {grace && (
          <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-white/70 p-2.5 text-left">
            <CheckCircle2 size={14} className="text-emerald-600 shrink-0" />
            <p className="text-xs font-semibold text-emerald-800">
              Anúncio indisponível na sua região — liberamos o próximo lote gratuitamente.
            </p>
          </div>
        )}

        <button
          type="button"
          onClick={handleWatch}
          disabled={busy}
          className="w-full bg-gradient-to-tr from-emerald-600 to-emerald-400 hover:brightness-105 disabled:opacity-50 text-neutral-950 font-black py-2.5 rounded-xl apple-spring shadow-md cursor-pointer active:scale-95"
        >
          {busy ? 'Carregando anúncio…' : 'Assistir Vídeo e Continuar'}
        </button>
      </div>
    </div>
  );
}
