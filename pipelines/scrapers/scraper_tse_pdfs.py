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

def extract_and_refine_pdfs() -> List[Document]:
    """
    TODO: Implementar extração de PDFs do TSE (Planos de Governo).
    1. Baixar PDFs.
    2. Realizar OCR/extração de texto.
    3. Passar pelo LLM para "Refinamento" (limpeza e formatação).
    4. Retornar lista de objetos Document (LangChain).
    """
    logging.info("Extraindo PDFs do TSE...")
    # Mock data
    docs = [
        Document(
            page_content="Proposta de governo do candidato X: melhorar a educação...",
            metadata={"source": "tse_pdf", "candidato": "Candidato X", "ano": 2026}
        )
    ]
    return docs

def main() -> None:
    logging.info("Iniciando pipeline do TSE (Planos de Governo)...")
    docs = extract_and_refine_pdfs()
    
    if docs:
        logging.info("Enviando documentos refinados para o Pinecone...")
        ingest_documents(docs)
        logging.info("Pipeline TSE concluída.")
    else:
        logging.warning("Nenhum documento gerado.")

if __name__ == "__main__":
    main()
