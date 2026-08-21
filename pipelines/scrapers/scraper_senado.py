import requests
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Configuração Básica de Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_URL_LEGIS = "https://legis.senado.leg.br/dadosabertos"
BASE_URL_ADM = "https://adm.senado.gov.br/adm-dadosabertos/api/v1"
DOCS_DIR = Path("data/docs")
DEFAULT_TIMEOUT = 30
HEADERS_JSON = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}


def fetch_senado_json(url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    """Realiza requisição HTTP GET para os serviços do Senado e retorna JSON."""
    try:
        response = requests.get(url, headers=HEADERS_JSON, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Erro ao acessar {url}: {e}")
        return None


def scrape_proposicoes(limit: int = 30) -> None:
    """Extrai proposições (matérias) em tramitação no Senado Federal."""
    logging.info("Buscando matérias em tramitação no Senado Federal...")
    url = f"{BASE_URL_LEGIS}/materia/tramitando"
    data = fetch_senado_json(url)
    if not data:
        return

    materias = (
        data.get("ListaMateriasTramitando", {})
        .get("Materias", {})
        .get("Materia", [])
    )
    if isinstance(materias, dict):
        materias = [materias]

    count = 0
    for mat in materias[:limit]:
        ident = mat.get("IdentificacaoMateria", {})
        mat_id = ident.get("CodigoMateria")
        if not mat_id:
            continue

        sigla = ident.get("SiglaSubtipoMateria", "")
        numero = ident.get("NumeroMateria", "")
        ano = ident.get("AnoMateria", "")
        titulo = f"{sigla} {numero}/{ano}".strip()
        
        dados_basicos = mat.get("DadosBasicosMateria", {})
        ementa = dados_basicos.get("EmentaMateria", "Sem ementa disponível.")
        natureza = dados_basicos.get("NaturezaMateria", {}).get("NomeNatureza", "N/A")
        autor = mat.get("Autoria", {}).get("Autor", {})
        nome_autor = autor.get("NomeAutor", "Autor desconhecido") if isinstance(autor, dict) else "Vários autores"

        md_content = "\n".join([
            f"[SENADO_PROPOSICAO: {titulo}]",
            f"# Proposição Senado: {titulo}",
            f"\n**Código da Matéria:** {mat_id}",
            f"\n**Natureza:** {natureza}",
            f"\n**Autor:** {nome_autor}",
            f"\n**Ementa:** {ementa}\n"
        ])

        filepath = DOCS_DIR / f"senado_proposicao_{mat_id}.md"
        filepath.write_text(md_content, encoding="utf-8")
        count += 1

    logging.info(f"Salvas {count} proposições do Senado.")


def scrape_votacoes(limit: int = 30) -> None:
    """Extrai deliberações e votações recentes do Senado Federal."""
    logging.info("Buscando votações recentes no Senado Federal...")
    url = f"{BASE_URL_LEGIS}/votacao"
    votacoes = fetch_senado_json(url)

    if not isinstance(votacoes, list):
        logging.warning("Formato inesperado para votações do Senado.")
        return

    count = 0
    for vot in votacoes[:limit]:
        ident = vot.get("identificacao") or f"Votação {vot.get('codigoSessaoVotacao', 'S/N')}"
        data_sessao = vot.get("dataSessao", "Data N/A")
        ementa = vot.get("ementa", "Ementa não informada.")
        resultado = vot.get("resultadoVotacao", "Desconhecido")
        
        sim = vot.get("totalVotosSim", 0)
        nao = vot.get("totalVotosNao", 0)
        abst = vot.get("totalVotosAbstencao", 0)

        md_lines = [
            f"[SENADO_VOTACAO: {ident}]",
            f"# Votação Senado: {ident}",
            f"\n**Data da Sessão:** {data_sessao}",
            f"\n**Ementa:** {ementa}",
            f"\n**Resultado:** {resultado} (Sim: {sim} | Não: {nao} | Abstenções: {abst})",
            "\n## Votos Individuais dos Senadores\n"
        ]

        votos_list = vot.get("votos", [])
        if isinstance(votos_list, list):
            for v in votos_list:
                nome = v.get("nomeParlamentar", "Desconhecido")
                partido = v.get("siglaPartidoParlamentar", "S/P")
                uf = v.get("siglaUFParlamentar", "S/UF")
                voto_parlamentar = v.get("siglaVotoParlamentar", "N/A")
                md_lines.append(f"- Senador **{nome}** ({partido}-{uf}): **{voto_parlamentar}**")

        vot_code = vot.get("codigoSessaoVotacao") or count
        filepath = DOCS_DIR / f"senado_votacao_{vot_code}.md"
        filepath.write_text("\n".join(md_lines), encoding="utf-8")
        count += 1

    logging.info(f"Salvas {count} votações do Senado.")


def scrape_discursos(limit_senadores: int = 15) -> None:
    """Extrai discursos/pronunciamentos recentes dos Senadores."""
    logging.info("Buscando discursos recentes dos Senadores...")
    url_senadores = f"{BASE_URL_LEGIS}/senador/lista/atual"
    data = fetch_senado_json(url_senadores)
    if not data:
        return

    senadores = (
        data.get("ListaParlamentarEmExercicio", {})
        .get("Parlamentares", {})
        .get("Parlamentar", [])
    )
    if isinstance(senadores, dict):
        senadores = [senadores]

    ano_atual = datetime.now().year
    data_inicio = f"{ano_atual - 2}-01-01"

    count = 0
    for sen in senadores[:limit_senadores]:
        p = sen.get("IdentificacaoParlamentar", {})
        cod = p.get("CodigoParlamentar")
        nome = p.get("NomeParlamentar", "Senador")
        partido = p.get("SiglaPartidoParlamentar", "S/P")
        uf = p.get("UfParlamentar", "S/UF")

        if not cod:
            continue

        url_disc = f"{BASE_URL_LEGIS}/senador/{cod}/discursos?dataInicio={data_inicio}"
        data_disc = fetch_senado_json(url_disc)
        if not data_disc:
            continue

        pronunciamentos = (
            data_disc.get("DiscursosParlamentar", {})
            .get("Parlamentar", {})
            .get("Pronunciamentos")
        )
        if not pronunciamentos or not isinstance(pronunciamentos, dict):
            continue

        items = pronunciamentos.get("Pronunciamento", [])
        if isinstance(items, dict):
            items = [items]

        if not items:
            continue

        md_lines = [
            f"[SENADO_DISCURSO: {nome}]",
            f"# Discursos do Senador {nome} ({partido}-{uf})",
            f"\n**Código do Senador:** {cod}",
            "\n## Pronunciamentos Recentes\n"
        ]

        for item in items[:10]:
            data_p = item.get("DataPronunciamento", "Data N/A")
            resumo = item.get("TextoResumo") or item.get("Indexacao") or "Sem resumo disponível."
            casa = item.get("SiglaCasaPronunciamento", "SF")
            md_lines.append(f"### Data: {data_p} ({casa})\n{resumo}\n")

        filepath = DOCS_DIR / f"senado_discursos_{cod}.md"
        filepath.write_text("\n".join(md_lines), encoding="utf-8")
        count += 1

    logging.info(f"Salvos discursos de {count} senadores.")


def scrape_ceaps(ano: Optional[int] = None, top_records: int = 500) -> None:
    """Extrai dados do uso da CEAPS (Cota Parlamentar) dos Senadores."""
    if ano is None:
        ano = datetime.now().year - 1

    logging.info(f"Buscando gastos da CEAPS (Cota Parlamentar) para o ano {ano}...")
    url = f"{BASE_URL_ADM}/senadores/despesas_ceaps/{ano}"
    data = fetch_senado_json(url)

    if not isinstance(data, list) or not data:
        logging.warning(f"Nenhum registro de CEAPS retornado para {ano}.")
        return

    # Agrupa gastos por senador
    gastos_por_senador: Dict[str, List[Dict[str, Any]]] = {}
    for record in data[:top_records]:
        nome = record.get("nomeSenador") or "DESPESAS_DIVERSAS"
        if nome not in gastos_por_senador:
            gastos_por_senador[nome] = []
        gastos_por_senador[nome].append(record)

    count = 0
    for nome_senador, lista_gastos in gastos_por_senador.items():
        total_gasto = sum(float(g.get("valorReembolsado", 0)) for g in lista_gastos)
        
        md_lines = [
            f"[SENADO_CEAPS: {nome_senador}]",
            f"# Uso da CEAPS (Cota Parlamentar) - {nome_senador} ({ano})",
            f"\n**Total Amostrado:** R$ {total_gasto:,.2f}",
            "\n## Detalhamento das Despesas Reembolsadas\n"
        ]

        for g in lista_gastos[:20]:
            data_g = g.get("data", "S/D")
            tipo = g.get("tipoDespesa", "Geral")
            fornecedor = g.get("fornecedor", "Desconhecido")
            valor = float(g.get("valorReembolsado", 0))
            detalhe = g.get("detalhamento") or ""
            info_detalhe = f" ({detalhe})" if detalhe else ""

            md_lines.append(
                f"- **{data_g}** | R$ {valor:,.2f} | **{tipo}** - Fornecedor: *{fornecedor}*{info_detalhe}"
            )

        safe_filename = "".join(c if c.isalnum() else "_" for c in nome_senador).strip("_")
        filepath = DOCS_DIR / f"senado_ceaps_{safe_filename}_{ano}.md"
        filepath.write_text("\n".join(md_lines), encoding="utf-8")
        count += 1

    logging.info(f"Salvos relatórios de CEAPS para {count} senadores.")


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    logging.info("--- Iniciando Scraper do Senado Federal ---")
    scrape_proposicoes()
    scrape_votacoes()
    scrape_discursos()
    scrape_ceaps()
    logging.info("--- Scraper do Senado Federal Concluído ---")


if __name__ == "__main__":
    main()
