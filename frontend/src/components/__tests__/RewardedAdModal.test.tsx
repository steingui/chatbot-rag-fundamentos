import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RewardedAdModal } from '../RewardedAdModal';
import { useChatStore } from '../../store/useChatStore';

describe('RewardedAdModal (MON-603 web)', () => {
  beforeEach(() => {
    localStorage.clear();
    useChatStore.setState({ adLocked: true, guestPromptCount: 3, isLoading: false });
  });

  it('renderiza o modal de recompensa quando adLocked', () => {
    render(<RewardedAdModal />);
    expect(screen.getByText(/Assistir Vídeo para Continuar/i)).toBeTruthy();
  });

  it('não exibe banner de antecipação de prompts restantes (paywall removido)', () => {
    useChatStore.setState({ adLocked: false, guestPromptCount: 2, isLoading: false });
    const { container } = render(<RewardedAdModal />);
    expect(container.querySelector('.bg-emerald-50')).toBeNull();
    expect(screen.queryByText(/prompt restante/i)).toBeNull();
  });

  it('destrava o próximo lote após assistir o anúncio (modo mock)', async () => {
    render(<RewardedAdModal />);
    const button = screen.getByRole('button', { name: /Assistir Vídeo/i });
    fireEvent.click(button);
    await waitFor(() => {
      expect(useChatStore.getState().adLocked).toBe(false);
    });
  });
});
