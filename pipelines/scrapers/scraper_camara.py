import requests
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
DOCS_DIR = Path("data/docs")
DEFAULT_ITEMS = 50
MAX_WORKERS = 5

def _get_resilient_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

_session = _get_resilient_session()


from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=False
)
def fetch_data(endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Faz a requisição para a API da Câmara e retorna a lista de dados com retries resilientes."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    try:
        response = _session.get(url, headers=headers, params=params, timeout=(10, 30))
        response.raise_for_status()
        return response.json().get("dados", [])
    except requests.RequestException as e:
        logging.error(f"Erro ao acessar {url}: {e}")
        return []


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(min=1, max=5),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=False
)
def fetch_proposicao_ementa(uri_proposicao: str) -> str:
    """Busca a ementa de uma proposição através de sua URI na API da Câmara com retries resilientes."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        response = _session.get(uri_proposicao, headers=headers, timeout=(10, 30))
        response.raise_for_status()
        dados = response.json().get("dados", {})
        return dados.get("ementa") or "Ementa indisponível."
    except requests.RequestException as e:
        logging.warning(f"Aviso: Falha ao buscar a proposição na URI {uri_proposicao}: {e}")
        return "Ementa indisponível (Erro na API)."



def get_recent_votacoes(limit: int = DEFAULT_ITEMS) -> List[Dict[str, Any]]:
    """Busca as votações mais recentes."""
    return fetch_data("votacoes", params={
        "ordem": "DESC",
        "ordenarPor": "dataHoraRegistro",
        "itens": limit
    })


def format_votacao_md(votacao: Dict[str, Any], votos: List[Dict[str, Any]]) -> str:
    """Formata os dados de uma votação e seus votos em Markdown."""
    votacao_id = votacao["id"]
    sigla = votacao.get("proposicaoObjeto") or f"Votação {votacao_id}"
    descricao = votacao.get("descricao", "Sem descrição disponível.")
    ementa = votacao.get("ementa", "Ementa não vinculada (Votação sem proposição base).")
    data_registro = votacao.get("dataHoraRegistro", "Data desconhecida")
    
    md_lines = [
        f"[TEMA: {sigla}]",
        f"# Votação: {sigla}",
        f"\n**Data:** {data_registro}",
        f"\n**Ementa (O que é a lei):** {ementa}",
        f"\n**Objeto da Votação:** {descricao}",
        "\n## Votos dos Deputados\n"
    ]
    
    for voto in votos:
        deputado = voto.get("deputado_", {}).get("nome", "Desconhecido")
        partido = voto.get("deputado_", {}).get("siglaPartido", "S/P")
        uf = voto.get("deputado_", {}).get("siglaUf", "S/UF")
        tipo_voto = voto.get("tipoVoto", "Abstenção")
        
        md_lines.append(f"- Sobre '{sigla}', o deputado **{deputado}** ({partido}-{uf}) votou **{tipo_voto}**.")
        
    return "\n".join(md_lines)


def process_single_votacao(votacao: Dict[str, Any]) -> Optional[tuple]:
    """Processa uma votação individualmente buscando votos e ementa."""
    votacao_id = votacao["id"]
    votos = fetch_data(f"votacoes/{votacao_id}/votos")
    if not votos:
        return None

    uri_proposicao = votacao.get("uriProposicaoObjeto")
    if uri_proposicao:
        votacao["ementa"] = fetch_proposicao_ementa(uri_proposicao)

    md_content = format_votacao_md(votacao, votos)
    return (votacao_id, md_content)


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Buscando as {DEFAULT_ITEMS} votações mais recentes em paralelo...")
    
    votacoes = get_recent_votacoes()
    count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_single_votacao, v) for v in votacoes]
        for future in as_completed(futures):
            res = future.result()
            if not res:
                continue

            votacao_id, md_content = res
            filepath = DOCS_DIR / f"votacao_{votacao_id}.md"
            filepath.write_text(md_content, encoding="utf-8")
            count += 1
        
    logging.info(f"Scraping concluído! {count} votações salvas.")


if __name__ == "__main__":
    main()
