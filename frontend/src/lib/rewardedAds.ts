export type AdProvider = 'gpt' | 'mock' | 'unavailable';

// MON-605: Fallback Engine — resolve o provider de anúncio no client web.
// 'gpt' = GPT Ads (provider padrão de produção via VITE_ADS_MODE).
// 'unavailable' = sem anúncio disponível na região → Free Grace (destrava sem vídeo).
// Qualquer outro valor/ausente → 'mock' (ambiente de dev/teste, zero dependência externa).
export const resolveAdProvider = (mode?: string): AdProvider => {
  const normalized = (mode || '').trim().toLowerCase();
  if (normalized === 'gpt') return 'gpt';
  if (normalized === 'unavailable') return 'unavailable';
  return 'mock';
};

export type RewardedAdResult =
  | { completed: true; provider: AdProvider }
  | { completed: false; provider: AdProvider; error: string };

// MON-601 (web): helper de exibição de Rewarded Ad com fallback gracioso.
// A imersão real (GPT Ads SDK) é injetada no host HTML em produção; aqui o client
// apenas resolve o provider e delega o "assistir" para o bridge global quando existir.
export async function showRewardedAd(
  provider: AdProvider = resolveAdProvider(import.meta.env?.VITE_ADS_MODE)
): Promise<RewardedAdResult> {
  if (provider === 'unavailable') {
    return { completed: true, provider };
  }

  try {
    // Bridge opcional injetado pelo host (ex.: GPT Ads). Sem ele, o mock completa.
    const bridge = (globalThis as Record<string, unknown>).__adsBridge as
      | { showRewarded?: () => Promise<boolean> }
      | undefined;

    if (provider === 'gpt' && bridge?.showRewarded) {
      const watched = await bridge.showRewarded();
      return watched
        ? { completed: true, provider }
        : { completed: false, provider, error: 'Ad não concluído pelo usuário.' };
    }

    // Mock: simula o usuário assistindo o vídeo até o fim.
    await new Promise((resolve) => setTimeout(resolve, 50));
    return { completed: true, provider };
  } catch (e) {
    // Fallback gracioso em falha de carregamento (Fill Rate limit).
    return {
      completed: false,
      provider,
      error: e instanceof Error ? e.message : 'Falha ao carregar o anúncio.'
    };
  }
}
