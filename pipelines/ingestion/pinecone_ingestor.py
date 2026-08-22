import os
import hashlib
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
    """Carrega PDFs e Markdown de um diretório, excluindo relatórios de saúde internos de CI/CD."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
        logging.warning(f"Diretório '{docs_path}' criado. Adicione documentos antes de ingerir.")
        return []

    pdf_loader = PyPDFDirectoryLoader(str(docs_path))
    md_loader = DirectoryLoader(str(docs_path), glob="**/*.md", loader_cls=TextLoader)
    
    docs = pdf_loader.load() + md_loader.load()
    # Filtra relatórios operacionais de CI/CD para manter a base política limpa para os usuários finais
    return [doc for doc in docs if not doc.metadata.get("source", "").endswith("pipeline_health_report.md")]


def generate_deterministic_id(doc, idx: int) -> str:
    """Gera um hash MD5 único e determinístico baseado na fonte e no conteúdo do chunk."""
    source = doc.metadata.get("source", "unknown_source")
    content_hash = hashlib.md5(doc.page_content.encode("utf-8")).hexdigest()[:12]
    raw_key = f"{source}::{idx}::{content_hash}"
    return hashlib.md5(raw_key.encode("utf-8")).hexdigest()


def limpar_vetores_antigos_por_fonte(sources: set) -> None:
    """Remove vetores antigos do Pinecone associados às fontes fornecidas antes da nova ingestão."""
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key or not sources:
        return

    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=api_key)
        index = pc.Index(INDEX_NAME)
        
        count = 0
        for src in sources:
            try:
                index.delete(filter={"source": {"$eq": src}})
                count += 1
            except Exception as e:
                logging.debug(f"Não foi possível apagar vetores antigos da fonte {src}: {e}")
        
        if count > 0:
            logging.info(f"Limpeza preventiva executada para {count} fontes de documentos.")
    except Exception as err:
        logging.warning(f"Aviso na pré-limpeza de vetores por fonte: {err}")


def ingest_documents(docs: list) -> None:
    """Recebe uma lista de documentos LangChain, limpa vetores antigos e realiza upsert no Pinecone."""
    if not os.environ.get("PINECONE_API_KEY"):
        logging.error("PINECONE_API_KEY não configurada no .env!")
        return

    if not docs:
        logging.warning("Nenhum documento para ingerir.")
        return

    # Extrai fontes únicas para apagar versões anteriores e evitar chunks órfãos
    unique_sources = set(doc.metadata.get("source") for doc in docs if doc.metadata.get("source"))
    limpar_vetores_antigos_por_fonte(unique_sources)

    logging.info(f"{len(docs)} documentos recebidos. Fatiando...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    splits = text_splitter.split_documents(docs)

    logging.info(f"Gerando embeddings (API HF) e enviando para o Pinecone (Index: {INDEX_NAME})...")
    embeddings = HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        huggingfacehub_api_token=os.environ.get("HF_TOKEN")
    )
    
    # Gerar IDs determinísticos para garantir idempotência
    ids = [generate_deterministic_id(doc, i) for i, doc in enumerate(splits)]

    vectorstore = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=embeddings
    )
    vectorstore.add_documents(documents=splits, ids=ids)
    logging.info(f"Ingestão e atualização de consistência concluídas! {len(splits)} chunks processados.")


def ingest_from_directory(docs_path: Path) -> None:
    """Fluxo completo: lê do diretório e ingere no Pinecone."""
    logging.info(f"Iniciando carregamento de documentos do diretório {docs_path}...")
    docs = carregar_documentos_diretorio(docs_path)
    ingest_documents(docs)


if __name__ == "__main__":
    DOCS_DIR = Path("data/docs")
    ingest_from_directory(DOCS_DIR)
