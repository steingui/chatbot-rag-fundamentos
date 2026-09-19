import { describe, it, expect, beforeEach } from 'vitest';
import {
  formatMarkdown,
  makeSession,
  PROMPTS_PER_BATCH,
  isAdLocked,
  promptsRemainingInBatch,
  useChatStore
} from '../useChatStore';

describe('useChatStore utilities & security', () => {
  it('cria uma sessão válida com estado inicial', () => {
    const session = makeSession(0);
    expect(session.label).toBe('Sessão 1');
    expect(session.messages.length).toBe(1);
    expect(session.messages[0].role).toBe('bot');
  });

  it('higieniza HTML e previne injeções XSS perigosas via DOMPurify', () => {
    const maliciousInput = '<script>alert("xss")</script>\n\n**Texto seguro**';
    const cleanOutput = formatMarkdown(maliciousInput);
    expect(cleanOutput).not.toContain('<script>');
    expect(cleanOutput).toContain('<strong>Texto seguro</strong>');
  });

  it('converte markdown em HTML com suporte a tabelas e negrito', () => {
    const markdown = '| Col 1 | Col 2 |\n| --- | --- |\n| Val 1 | Val 2 |';
    const html = formatMarkdown(markdown);
    expect(html).toContain('<th>Col 1</th>');
    expect(html).toContain('<td>Val 1</td>');
  });
});

describe('MON-602 contador de prompts / rewarded ads', () => {
  beforeEach(() => {
    localStorage.clear();
    useChatStore.setState({ guestPromptCount: 0, adLocked: false });
  });

  it('expõe o tamanho do lote como 3 prompts', () => {
    expect(PROMPTS_PER_BATCH).toBe(3);
  });

  it('libera os 3 primeiros prompts sem exigir anúncio', () => {
    expect(isAdLocked(0)).toBe(false);
    expect(isAdLocked(1)).toBe(false);
    expect(isAdLocked(2)).toBe(false);
  });

  it('trava após o 3º prompt consumido', () => {
    expect(isAdLocked(3)).toBe(true);
    expect(isAdLocked(6)).toBe(true);
    expect(isAdLocked(9)).toBe(true);
  });

  it('calcula prompts restantes no lote atual', () => {
    expect(promptsRemainingInBatch(0)).toBe(3);
    expect(promptsRemainingInBatch(1)).toBe(2);
    expect(promptsRemainingInBatch(2)).toBe(1);
    expect(promptsRemainingInBatch(3)).toBe(0);
    expect(promptsRemainingInBatch(4)).toBe(2);
    expect(promptsRemainingInBatch(6)).toBe(0);
  });

  it('incrementa o contador e trava o store no 3º prompt', () => {
    const { incrementGuestPrompts } = useChatStore.getState();
    incrementGuestPrompts();
    incrementGuestPrompts();
    expect(useChatStore.getState().adLocked).toBe(false);
    incrementGuestPrompts();
    expect(useChatStore.getState().guestPromptCount).toBe(3);
    expect(useChatStore.getState().adLocked).toBe(true);
  });

  it('destrava o próximo lote ao assistir 1 rewarded ad', () => {
    useChatStore.setState({ guestPromptCount: 3, adLocked: true });
    useChatStore.getState().unlockRewardedAd();
    expect(useChatStore.getState().adLocked).toBe(false);
    expect(useChatStore.getState().guestPromptCount).toBe(3);
  });

  it('resetGuestPrompts zera contador e destrava', () => {
    useChatStore.setState({ guestPromptCount: 6, adLocked: true });
    useChatStore.getState().resetGuestPrompts();
    expect(useChatStore.getState().guestPromptCount).toBe(0);
    expect(useChatStore.getState().adLocked).toBe(false);
  });

  it('bloqueia envio de novo prompt enquanto adLocked (MON-603 guard)', async () => {
    useChatStore.setState({ guestPromptCount: 3, adLocked: true, isLoading: false });
    await useChatStore.getState().sendMessageStream('bloqueado?');
    expect(useChatStore.getState().guestPromptCount).toBe(3);
  });
});
