import { describe, it, expect } from 'vitest';
import { stageLabel } from '../useChatStore';

describe('stageLabel — feedback granular por etapa do SSE (finding 2)', () => {
  it('mapeia etapa de busca', () => {
    expect(stageLabel('retrieving')).toContain('Buscando');
  });

  it('mapeia etapa de geração', () => {
    expect(stageLabel('generating')).toContain('Gerando');
  });

  it('retorna rótulo padrão para estágios desconhecidos', () => {
    expect(stageLabel('qualquer')).toContain('Consultando');
  });
});
