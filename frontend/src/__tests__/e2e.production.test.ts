// E2E de integração do frontend contra os ambientes produtivos:
// - Firebase Hosting (frontend): https://rag-eleicoes.web.app
// - Cloud Run (backend API): https://chatbot-rag-api-...run.app
//
// Valida o contrato real consumido por useChatStore.sendMessageStream()
// (healthcheck, POST /api/v1/chat e SSE /api/v1/chat/stream).
//
// Execução opt-in — NÃO roda no `npm run test` por padrão:
//
//   RUN_E2E_PROD=1 npm run test
//
// Variáveis opcionais: E2E_PROD_FRONTEND_URL e E2E_PROD_API_URL.
import { describe, it, expect } from 'vitest';

const FRONTEND_PROD_URL =
  process.env.E2E_PROD_FRONTEND_URL || 'https://rag-eleicoes.web.app';
const API_PROD_URL =
  process.env.E2E_PROD_API_URL ||
  'https://chatbot-rag-api-1043919586992.southamerica-east1.run.app';

const runProd = process.env.RUN_E2E_PROD === '1';

describe.skipIf(!runProd)('E2E produção (Firebase Hosting + Cloud Run)', () => {
  it('frontend prod serve o app React', async () => {
    const res = await fetch(`${FRONTEND_PROD_URL}/`);
    expect(res.ok).toBe(true);
    const html = await res.text();
    expect(html).toContain('<div id="root"></div>');
    expect(html).toContain('rag_politico');
  });

  it('backend prod responde healthcheck', async () => {
    const res = await fetch(`${API_PROD_URL}/`);
    expect(res.ok).toBe(true);
    const body = await res.json();
    expect(body.status).toBe('ok');
  });

  it('backend prod responde /api/v1/chat com answer e sources', async () => {
    const res = await fetch(`${API_PROD_URL}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'e2e_prod_front',
        query: 'Olá, tudo bem?',
        model: 'gemini-3.7-flash',
      }),
    });
    expect(res.ok).toBe(true);
    const body = await res.json();
    expect(typeof body.answer).toBe('string');
    expect(body.answer.length).toBeGreaterThan(0);
    expect(Array.isArray(body.sources)).toBe(true);
  });

  it('backend prod emite SSE com evento sources e [DONE]', async () => {
    const res = await fetch(`${API_PROD_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'e2e_prod_front',
        query: 'Olá',
        model: 'gemini-3.7-flash',
      }),
    });
    expect(res.ok).toBe(true);
    const raw = await res.text();
    expect(raw).toContain('"type": "sources"');
    expect(raw).toContain('data: [DONE]');
  });
});
