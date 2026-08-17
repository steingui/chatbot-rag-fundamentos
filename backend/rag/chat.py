import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

# Configuração Básica
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

# Constantes
DB_DIR = Path("data/chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "meta-llama/llama-3-8b-instruct:free"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

def build_rag_chain() -> Runnable:
    """Constrói e retorna a chain do RAG configurada."""
    if not DB_DIR.exists():
        raise FileNotFoundError(f"Vector DB '{DB_DIR}' não encontrado. Execute o script de ingestão primeiro.")

    logging.info("Carregando Vector DB e conectando ao LLM...")
    
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    llm = ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openai_api_base=OPENROUTER_BASE
    )

    system_prompt = (
        "Você é um assistente útil. Use o contexto fornecido para responder à pergunta. "
        "Se não souber a resposta com base no contexto, diga que não sabe.\n\n"
        "Contexto:\n{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

def iniciar_chat(rag_chain: Runnable) -> None:
    """Loop principal de interação do terminal."""
    print("\nChatbot RAG inicializado. Digite 'sair' para encerrar.")
    
    while True:
        try:
            user_input = input("\nVocê: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["sair", "exit", "quit"]:
                break

            response = rag_chain.invoke({"input": user_input})
            print(f"\nBot: {response['answer']}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Erro durante a geração da resposta: {e}")

def main() -> None:
    try:
        chain = build_rag_chain()
        iniciar_chat(chain)
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    main()
