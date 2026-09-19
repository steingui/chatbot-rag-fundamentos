import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const read = (rel: string) =>
  readFileSync(fileURLToPath(new URL(rel, import.meta.url)), 'utf8');

const exists = (rel: string) =>
  existsSync(fileURLToPath(new URL(rel, import.meta.url)));

describe('design system: tokens canônicos (tema claro produtivo)', () => {
  const indexCss = read('../../index.css');
  const tailwindConfig = read('../../../tailwind.config.js');

  it('define a paleta canônica como CSS variables em :root', () => {
    expect(indexCss).toContain('--color-canvas: #F2F2F7');
    expect(indexCss).toContain('--color-surface: #F4F4F6');
    expect(indexCss).toContain('--color-card: #FFFFFF');
    expect(indexCss).toContain('--color-ink: #1D1D1F');
    expect(indexCss).toContain('--color-accent: #10B981');
    expect(indexCss).toContain('--color-accent-strong: #059669');
    expect(indexCss).toContain('--color-danger: #E11D48');
  });

  it('define as fontes canônicas', () => {
    expect(indexCss).toContain("--font-sans: 'Plus Jakarta Sans'");
    expect(indexCss).toContain("--font-mono: 'JetBrains Mono'");
  });

  it('tailwind.config.js consome os tokens via var(--color-*)', () => {
    expect(tailwindConfig).toContain("canvas: 'var(--color-canvas)'");
    expect(tailwindConfig).toContain("surface: 'var(--color-surface)'");
    expect(tailwindConfig).toContain("ink: 'var(--color-ink)'");
    expect(tailwindConfig).toContain("accent: 'var(--color-accent)'");
  });

  it('removeu os artefatos legados de tema (dark theme morto)', () => {
    expect(exists('../tokens.css')).toBe(false);
    expect(exists('../tokens.ts')).toBe(false);
    expect(exists('../../App.css')).toBe(false);
    expect(exists('../../components/IntroModal.css')).toBe(false);
  });
});
