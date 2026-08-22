import { describe, it, expect } from 'vitest';
import { formatMarkdown, makeSession } from '../useChatStore';

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
