import os
import re
import logging
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
DOCS_DIR = Path("data/docs")

RSS_FEEDS = [
    {"nome": "G1 Fato ou Fake", "url": "https://g1.globo.com/rss/g1/fato-ou-fake/"},
    {"nome": "Estadão Verifica", "url": "https://politica.estadao.com.br/blogs/estadao-verifica/feed/"},
    {"nome": "Agência Pública", "url": "https://apublica.org/feed/"},
    {"nome": "Aos Fatos", "url": "https://www.aosfatos.org/noticias/feed/"}
]

def clean_html(raw_html: str) -> str:
    """Remove tags HTML simples para deixar o texto mais legível."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def fetch_rss_feeds() -> None:
    """Baixa feeds RSS de agências de checagem e salva como Markdown."""
    for feed in RSS_FEEDS:
        logging.info(f"Buscando feed RSS: {feed['nome']} ({feed['url']})")
        try:
            response = requests.get(feed['url'], timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            count = 0
            for item in root.findall('./channel/item'):
                title = item.findtext('title') or "Sem Título"
                link = item.findtext('link') or "Sem link"
                description_html = item.findtext('description') or ""
                description = clean_html(description_html)
                
                # Usa um hash do link para o nome do arquivo, garantindo unicidade
                file_id = hash(link)
                filepath = DOCS_DIR / f"factcheck_{abs(file_id)}.md"
                
                md_content = f"[TEMA: FACT-CHECKING]\n# {title}\n\n**Fonte:** {feed['nome']}\n**Link:** {link}\n\n**Checagem / Resumo:**\n{description}\n"
                
                filepath.write_text(md_content, encoding="utf-8")
                count += 1
                
                if count >= 20: # Limita a 20 notícias recentes por feed
                    break
                    
            logging.info(f"Salvos {count} arquivos de fact-checking do feed {feed['nome']}.")
            
        except Exception as e:
            logging.error(f"Erro ao processar RSS {feed['nome']}: {e}")

def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    logging.info("Iniciando pipeline de Fact-Checking (RSS)...")
    fetch_rss_feeds()
    logging.info("Pipeline RSS concluída.")

if __name__ == "__main__":
    main()
