import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';
import { resolveRoute } from '../routes';
import { PrivacyPage } from '../pages/PrivacyPage';

describe('SEC-504: Página de Privacidade e Termos de Uso', () => {
  it('resolve /privacidade para a PrivacyPage', () => {
    const route = resolveRoute('/privacidade');
    expect(route.type).toBe(PrivacyPage);
  });

  it('resolve rota desconhecida para o App (chat)', () => {
    const route = resolveRoute('/');
    expect(route.type).toBe(App);
  });

  it('renderiza Política de Privacidade e Termos de Uso', () => {
    render(<PrivacyPage />);
    expect(screen.getByRole('heading', { name: /Política de Privacidade/i })).toBeTruthy();
    expect(screen.getByRole('heading', { name: /Termos de Uso/i })).toBeTruthy();
  });

  it('cobre conformidade LGPD e exclusão de dados', () => {
    render(<PrivacyPage />);
    expect(screen.getAllByText(/LGPD/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/exclusão/i).length).toBeGreaterThan(0);
  });
});
