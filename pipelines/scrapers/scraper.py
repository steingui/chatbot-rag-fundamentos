import requests
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
DOCS_DIR = Path("data/docs")
DEFAULT_ITEMS = 50

def fetch_data(endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Faz a requisição para a API da Câmara e retorna a lista de dados."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        return response.json().get("dados", [])
    except requests.RequestException as e:
        logging.error(f"Erro ao acessar {url}: {e}")
        return []

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
    data_registro = votacao.get("dataHoraRegistro", "Data desconhecida")
    
    md_lines = [
        f"# Votação: {sigla}",
        f"\n**Data:** {data_registro}",
        f"\n**Descrição:** {descricao}",
        "\n## Votos dos Deputados\n"
    ]
    
    for voto in votos:
        deputado = voto.get("deputado_", {}).get("nome", "Desconhecido")
        partido = voto.get("deputado_", {}).get("siglaPartido", "S/P")
        uf = voto.get("deputado_", {}).get("siglaUf", "S/UF")
        tipo_voto = voto.get("tipoVoto", "Abstenção")
        
        md_lines.append(f"- O deputado **{deputado}** ({partido}-{uf}) votou **{tipo_voto}**.")
        
    return "\n".join(md_lines)

def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Buscando as {DEFAULT_ITEMS} votações mais recentes...")
    
    votacoes = get_recent_votacoes()
    
    for votacao in votacoes:
        votacao_id = votacao["id"]
        logging.info(f"Processando votação: {votacao_id}")

        votos = fetch_data(f"votacoes/{votacao_id}/votos")
        if not votos:
            logging.warning(f"Sem votos para a votação {votacao_id}. Pulando.")
            continue
            
        md_content = format_votacao_md(votacao, votos)
        
        filepath = DOCS_DIR / f"votacao_{votacao_id}.md"
        filepath.write_text(md_content, encoding="utf-8")
        logging.info(f"Arquivo gerado: {filepath}")
        
    logging.info("Scraping concluído!")

if __name__ == "__main__":
    main()
