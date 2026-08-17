import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEndpointEmbeddings

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

# Constantes
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def carregar_documentos_diretorio(docs_path: Path) -> list:
    """Carrega PDFs e Markdown de um diretório."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
        logging.warning(f"Diretório '{docs_path}' criado. Adicione documentos antes de ingerir.")
        return []

    pdf_loader = PyPDFDirectoryLoader(str(docs_path))
    md_loader = DirectoryLoader(str(docs_path), glob="**/*.md", loader_cls=TextLoader)
    
    return pdf_loader.load() + md_loader.load()

def ingest_documents(docs: list) -> None:
    """Recebe uma lista de documentos LangChain, gera embeddings e envia ao Pinecone."""
    if not os.environ.get("PINECONE_API_KEY"):
        logging.error("PINECONE_API_KEY não configurada no .env!")
        return

    if not docs:
        logging.warning("Nenhum documento para ingerir.")
        return

    logging.info(f"{len(docs)} documentos recebidos. Fatiando...")
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

def ingest_from_directory(docs_path: Path) -> None:
    """Fluxo completo: lê do diretório e ingere no Pinecone."""
    logging.info(f"Iniciando carregamento de documentos do diretório {docs_path}...")
    docs = carregar_documentos_diretorio(docs_path)
    ingest_documents(docs)

if __name__ == "__main__":
    # Compatibilidade: roda direto no diretório padrao se executado como script
    DOCS_DIR = Path("data/docs")
    ingest_from_directory(DOCS_DIR)
