import logging
from typing import List
from langchain_core.documents import Document
import sys
from pathlib import Path

# Adicionar a raiz do projeto no path para importar o ingestor
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from pipelines.ingestion.pinecone_ingestor import ingest_documents

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def fetch_rss_feeds() -> List[Document]:
    """
    TODO: Implementar coleta de Feeds RSS (ex: Agência Lupa, Aos Fatos).
    1. Ler URLs de RSS.
    2. Extrair título, link e descrição das checagens de fatos.
    3. Retornar lista de objetos Document (LangChain).
    """
    logging.info("Buscando Feeds RSS de Fact-Checking...")
    # Mock data
    docs = [
        Document(
            page_content="FALSO: É mentira que a PEC 45/2019 aumenta impostos sobre cestas básicas.",
            metadata={"source": "lupa_rss", "link": "https://lupa.uol.com.br/...", "data": "2023-10-01"}
        )
    ]
    return docs

def main() -> None:
    logging.info("Iniciando pipeline de Fact-Checking (RSS)...")
    docs = fetch_rss_feeds()
    
    if docs:
        logging.info("Enviando checagens de fatos para o Pinecone...")
        ingest_documents(docs)
        logging.info("Pipeline RSS concluída.")
    else:
        logging.warning("Nenhuma checagem encontrada.")

if __name__ == "__main__":
    main()
