import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

# Constantes de Diretório atualizadas para a estrutura monorepo
DOCS_DIR = Path("data/docs")
DB_DIR = Path("data/chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def carregar_documentos(docs_path: Path) -> list:
    """Carrega PDFs e MDs do diretório informado."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
        logging.warning(f"Diretório '{docs_path}' criado. Adicione documentos antes de ingerir.")
        return []

    pdf_loader = PyPDFDirectoryLoader(str(docs_path))
    md_loader = DirectoryLoader(str(docs_path), glob="**/*.md")
    
    return pdf_loader.load() + md_loader.load()

def processar_ingestao() -> None:
    """Executa o pipeline completo de ingestão de documentos."""
    logging.info("Iniciando carregamento de documentos...")
    docs = carregar_documentos(DOCS_DIR)
    
    if not docs:
        logging.warning("Nenhum documento encontrado para ingestão.")
        return

    logging.info(f"{len(docs)} documentos carregados. Dividindo em chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )
    splits = text_splitter.split_documents(docs)

    logging.info(f"Gerando embeddings e persistindo no ChromaDB em '{DB_DIR}'...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    Chroma.from_documents(
        documents=splits, 
        embedding=embeddings, 
        persist_directory=str(DB_DIR)
    )
    logging.info("Ingestão concluída com sucesso!")

def main() -> None:
    processar_ingestao()

if __name__ == "__main__":
    main()
