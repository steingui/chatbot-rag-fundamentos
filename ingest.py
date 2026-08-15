import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

DOCS_DIR = "docs"
DB_DIR = "chroma_db"

def main():
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"Diretório '{DOCS_DIR}' criado. Adicione seus PDFs ou MDs nele.")
        return

    print("Carregando documentos...")
    pdf_loader = PyPDFDirectoryLoader(DOCS_DIR)
    md_loader = DirectoryLoader(DOCS_DIR, glob="**/*.md")
    
    docs = pdf_loader.load() + md_loader.load()
    if not docs:
        print("Nenhum documento encontrado.")
        return

    print(f"{len(docs)} documentos carregados. Dividindo em chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    print(f"Gerando embeddings e salvando no ChromaDB em '{DB_DIR}'...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=DB_DIR)
    print("Ingestão concluída com sucesso!")

if __name__ == "__main__":
    main()
