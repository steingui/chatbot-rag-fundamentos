import os
import logging
from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "meta-llama/llama-3-8b-instruct:free"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")

def build_rag_chain() -> Runnable:
    if not os.environ.get("PINECONE_API_KEY"):
        raise ValueError("PINECONE_API_KEY não configurada no .env!")

    logging.info(f"Conectando ao Pinecone (Index: {INDEX_NAME}) e ao LLM...")
    
    embeddings = HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        huggingfacehub_api_token=os.environ.get("HF_TOKEN")
    )
    vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
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
    print("\nChatbot RAG conectado ao Pinecone. Digite 'sair' para encerrar.")
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
            logging.error(f"Erro: {e}")

def main() -> None:
    try:
        chain = build_rag_chain()
        iniciar_chat(chain)
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    main()
