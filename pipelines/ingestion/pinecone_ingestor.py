import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))

import os
import hashlib
import logging
import re
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_core.documents import Document

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

# Constantes
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")
CHUNK_SIZE = 1000
OVERLAP_SENTENCES = 1

_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')
_DATE_RE = re.compile(r'(\d{4})[_-](\d{2})[_-](\d{2})')

_DOC_TYPE_RULES = [
    ("tse_bens", "tse_bens"),
    ("votacao_", "votacao"),
    ("senado", "senado"),
    ("transparencia", "transparencia"),
    ("cgu", "transparencia"),
    ("lupa", "fact_check"),
    ("aosfatos", "fact_check"),
    ("proposicao", "proposicao"),
    ("camara", "proposicao"),
    ("plano_governo", "plano_governo"),
]


def _split_sentences(text: str) -> list:
    """Divide o texto em sentenças completas (nunca corta a frase no meio)."""
    return [part.strip() for part in _SENTENCE_SPLIT_RE.split(text.strip()) if part.strip()]


def _chunk_sentences(sentences: list, chunk_size: int = CHUNK_SIZE, overlap_sentences: int = OVERLAP_SENTENCES) -> list:
    """Agrupa sentenças em chunks por orçamento de caracteres, com overlap de sentenças nas bordas."""
    chunks: list = []
    buffer = ""
    buffer_sentences: list = []

    for sentence in sentences:
        if buffer and len(buffer) + len(sentence) + 1 > chunk_size:
            chunks.append(buffer)
            tail = buffer_sentences[-overlap_sentences:] if overlap_sentences > 0 else []
            buffer = " ".join(tail)
            buffer_sentences = list(tail)

        buffer = f"{buffer} {sentence}".strip() if buffer else sentence
        buffer_sentences.append(sentence)

    if buffer:
        chunks.append(buffer)
    return chunks


def enrich_metadata(meta: dict) -> dict:
    """Enriquece metadata do chunk com doc_type, title e date para filtro pré-busca/rerank."""
    enriched = dict(meta)
    source = str(meta.get("source", ""))
    source_lower = source.lower()

    for keyword, doc_type in _DOC_TYPE_RULES:
        if keyword in source_lower:
            enriched["doc_type"] = doc_type
            break
    else:
        enriched["doc_type"] = "interno"

    enriched.setdefault("title", Path(source).stem if source else "unknown")

    match = _DATE_RE.search(source)
    if match:
        enriched["date"] = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    return enriched


def _chunk_documents(docs: list) -> list:
    """Chunk semântico por sentenças + metadata enriquecida (doc_type/title/date)."""
    chunks = []
    for doc in docs:
        sentences = _split_sentences(doc.page_content)
        for text in _chunk_sentences(sentences):
            chunks.append(Document(page_content=text, metadata=enrich_metadata(doc.metadata)))
    return chunks


def carregar_documentos_diretorio(docs_path: Path) -> list:
    """Carrega PDFs e Markdown de um diretório, excluindo relatórios de saúde internos de CI/CD."""
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
        logging.warning(f"Diretório '{docs_path}' criado. Adicione documentos antes de ingerir.")
        return []

    pdf_loader = PyPDFDirectoryLoader(str(docs_path))
    md_loader = DirectoryLoader(str(docs_path), glob="**/*.md", loader_cls=TextLoader)
    
    return pdf_loader.load() + md_loader.load()


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

    logging.info(f"{len(docs)} documentos recebidos. Fatiando semanticamente...")
    splits = _chunk_documents(docs)

    logging.info(f"Gerando embeddings (API HF) e enviando para o Pinecone (Index: {INDEX_NAME})...")
    embeddings = HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        huggingfacehub_api_token=os.environ.get("HF_TOKEN")
    )
    
    # Gerar IDs determinísticos para garantir idempotência
    ids = [generate_deterministic_id(doc, i) for i, doc in enumerate(splits)]

    from pinecone import Pinecone
    from langchain_community.retrievers import PineconeHybridSearchRetriever
    from backend.rag.sparse_encoder import FastBM25Encoder

    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(INDEX_NAME)
    
    bm25_encoder = FastBM25Encoder()

    retriever = PineconeHybridSearchRetriever(
        embeddings=embeddings,
        sparse_encoder=bm25_encoder,
        index=index
    )

    logging.info(f"Fazendo upsert de {len(splits)} chunks híbridos (Densos + Esparsos/BM25)...")
    texts = [doc.page_content for doc in splits]
    metadatas = [doc.metadata for doc in splits]
    retriever.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    
    logging.info("Ingestão Híbrida concluída com sucesso.")


def ingest_from_directory(docs_path: Path) -> None:
    """Fluxo completo: lê do diretório e ingere no Pinecone."""
    logging.info(f"Iniciando carregamento de documentos do diretório {docs_path}...")
    docs = carregar_documentos_diretorio(docs_path)
    ingest_documents(docs)


if __name__ == "__main__":
    DOCS_DIR = Path("data/docs")
    ingest_from_directory(DOCS_DIR)
