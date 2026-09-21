// SEO/Perf estático — findings 1, 3, 5 e 7 da issue #13.
// Valida o HTML servido (index.html) e o CSS de entrada (index.css) sem depender
// de rede: checamos as tags/meta exatas que o auditor apontou como ausentes.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { describe, it, expect } from 'vitest';

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(resolve(here, '../../index.html'), 'utf-8');
const css = readFileSync(resolve(here, '../index.css'), 'utf-8');

describe('finding 1 — fontes sem @import render-blocking', () => {
  it('index.css não usa @import do Google Fonts', () => {
    expect(css).not.toContain('@import');
  });

  it('index.html emite preconnect para fonts.googleapis.com', () => {
    expect(html).toContain('fonts.googleapis.com');
    expect(html).toContain('rel="preconnect"');
  });

  it('index.html emite preconnect crossorigin para fonts.gstatic.com', () => {
    expect(html).toContain('fonts.gstatic.com');
    expect(html).toContain('crossorigin');
  });

  it('index.html carrega a folha de fontes via <link rel="stylesheet">', () => {
    expect(html).toContain('rel="stylesheet"');
  });
});

describe('finding 3/7 — social cards com imagem e robots', () => {
  it('define og:image', () => {
    expect(html).toContain('property="og:image"');
  });

  it('define og:image:width e og:image:height', () => {
    expect(html).toContain('property="og:image:width"');
    expect(html).toContain('property="og:image:height"');
  });

  it('define twitter:image', () => {
    expect(html).toContain('name="twitter:image"');
  });

  it('usa twitter:card summary_large_image', () => {
    expect(html).toContain('content="summary_large_image"');
  });

  it('define meta robots index,follow', () => {
    expect(html).toContain('name="robots"');
    expect(html).toContain('content="index,follow"');
  });
});

describe('finding 5 — JSON-LD WebSite/SearchAction', () => {
  it('emite bloco application/ld+json', () => {
    expect(html).toContain('application/ld+json');
  });

  it('declara potentialAction SearchAction', () => {
    expect(html).toContain('SearchAction');
  });
});
