# Persona: Jornalista Investigativo / Checador de Fatos

- **Nome**: Mariana Costa
- **Perfil**: Jornalista de veículos de imprensa e plataformas de fact-checking focada em apuração de dados eleitorais e legislativos.
- **Conhecimento Técnico**: Médio/Alto (familiarizada com dados públicos, diários oficiais e estatísticas eleitorais).
- **Estilo de Comunicação**: Exigente, analítica e focada em comprovação documental.

---

## Objetivos no Produto
1. Verificar a veracidade de declarações e históricos de votações de parlamentares.
2. Exigir links e referências diretas das fontes oficiais (TSE, Câmara, Senado, Querido Diário).
3. Detectar incongruências ou divergências de dados entre discursos e votos nominais.

---

## Cenários de Teste & Critérios de Bug
- **Bug de RAG / Fontes**: Resposta do modelo sem lista de fontes (`sources`) ou com links inválidos/quebrados.
- **Bug de Alucinação**: Afirmações de votações ou propostas que não constam nas fontes retornadas pelo RAG.
- **Bug de Rastreamento**: Presença de parâmetros sujos de UTM ou rastreadores nas URLs de origem.

---

## Template de Prompt Tipico
> "Quais foram os votos do senador [Nome] em projetos sobre transparência pública nos últimos 2 anos? Apresente os links oficiais das votações."
