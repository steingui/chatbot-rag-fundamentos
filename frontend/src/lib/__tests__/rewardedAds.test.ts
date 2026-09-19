import { describe, it, expect } from 'vitest';
import { resolveAdProvider } from '../rewardedAds';

describe('rewardedAds (web) — resolução de provider', () => {
  it('resolve mock como default e para valores desconhecidos', () => {
    expect(resolveAdProvider(undefined)).toBe('mock');
    expect(resolveAdProvider('')).toBe('mock');
    expect(resolveAdProvider('mock')).toBe('mock');
    expect(resolveAdProvider('banana')).toBe('mock');
  });

  it('resolve gpt quando VITE_ADS_MODE=gpt', () => {
    expect(resolveAdProvider('gpt')).toBe('gpt');
  });

  it('resolve unavailable quando VITE_ADS_MODE=unavailable (fallback gracioso)', () => {
    expect(resolveAdProvider('unavailable')).toBe('unavailable');
  });
});
