import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEndpointEmbeddings

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

# Constantes
DOCS_DIR = Path("data/docs")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def carregar_documentos(docs_path: Path) -> list:
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
        logging.warning(f"Diretório '{docs_path}' criado. Adicione documentos antes de ingerir.")
        return []

    pdf_loader = PyPDFDirectoryLoader(str(docs_path))
    md_loader = DirectoryLoader(str(docs_path), glob="**/*.md")
    
    return pdf_loader.load() + md_loader.load()

def processar_ingestao() -> None:
    if not os.environ.get("PINECONE_API_KEY"):
        logging.error("PINECONE_API_KEY não configurada no .env!")
        return

    logging.info("Iniciando carregamento de documentos...")
    docs = carregar_documentos(DOCS_DIR)
    
    if not docs:
        logging.warning("Nenhum documento encontrado.")
        return

    logging.info(f"{len(docs)} documentos carregados. Fatiando...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    splits = text_splitter.split_documents(docs)

    logging.info(f"Gerando embeddings (API HF) e enviando para o Pinecone (Index: {INDEX_NAME})...")
    embeddings = HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        huggingfacehub_api_token=os.environ.get("HF_TOKEN")
    )
    
    PineconeVectorStore.from_documents(
        documents=splits, 
        embedding=embeddings, 
        index_name=INDEX_NAME
    )
    logging.info("Ingestão concluída com sucesso no Pinecone!")

def main() -> None:
    processar_ingestao()

if __name__ == "__main__":
    main()
