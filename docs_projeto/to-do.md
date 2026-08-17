# Planejamento de Scraping e Evolução (Eleições 2026)

## Scraping de Fontes de Dados (Pipeline Automática)
- [ ] **Planos de Governo (TSE - DivulgaCand)**
  - Extrair PDFs/textos das propostas oficiais de presidenciáveis/governadores.
  - Refinar o texto (limpeza) via LLM antes de salvar em Markdown.
- [x] **Histórico de Votações (Câmara/Senado)**
  - Consumir API de Dados Abertos.
  - Mapear votos em pautas polêmicas (reformas, meio ambiente, economia) dos candidatos à reeleição.
- [ ] **Fact-Checking (Lupa, Aos Fatos)**
  - Coletar RSS feeds/scraping de checagem de discursos recentes.
  - Estruturar os fatos validados no VectorDB para o LLM não alucinar.
- [ ] **Declaração de Bens e Financiamento (TSE)**
  - Capturar evolução patrimonial e lista de principais doadores das campanhas.

## Evolução da Arquitetura
- [x] Criar script `scraper.py` (BeautifulSoup/requests).
- [ ] Criar etapa de "Refinamento" (usar LLM para formatar os dados crus em Markdown padronizado).
- [x] Acionar o `ingest.py` automaticamente após o scrapping (Via Actions em breve).
- [x] Construir Backend (ex: FastAPI ou Flask) para expor a lógica do `chat.py` via REST API.
- [ ] Construir Frontend para consumir a API (interface de chat interativa na web).
