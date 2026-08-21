import os
import logging
from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "google/gemma-4-31b-it:free"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")

_retriever = None
_llm = None
_session_chains = {}

def init_components():
    global _retriever, _llm
    if not os.environ.get("PINECONE_API_KEY"):
        raise ValueError("PINECONE_API_KEY não configurada no .env!")

    logging.info(f"Conectando ao Pinecone (Index: {INDEX_NAME}) e ao LLM...")
    
    embeddings = HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        huggingfacehub_api_token=os.environ.get("HF_TOKEN")
    )
    vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    _retriever = vectorstore.as_retriever(search_kwargs={"k": 15})

    _llm = ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openai_api_base=OPENROUTER_BASE
    )

def get_rag_chain(session_id: str = "default"):
    if _llm is None:
        init_components()

    if session_id in _session_chains:
        return _session_chains[session_id]

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

    system_prompt = (
        "Você é um assistente útil. Use o contexto fornecido para responder à pergunta.\n"
        "REGRA CRÍTICA: Se questionado sobre listas de deputados, votos, ou matemática, "
        "se os dados não estiverem COMPLETAMENTE listados no contexto, NUNCA invente nomes. "
        "Diga exatamente o que encontrou.\n\n"
        "Contexto:\n{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=_llm,
        retriever=_retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": prompt}
    )
    
    _session_chains[session_id] = qa_chain
    return qa_chain

def iniciar_chat() -> None:
    print("\nChatbot RAG conectado ao Pinecone. Digite 'sair' para encerrar.")
    while True:
        try:
            user_input = input("\nVocê: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["sair", "exit", "quit"]:
                break

            chain = get_rag_chain("cli-session")
            response = chain.invoke({"question": user_input})
            print(f"\nBot: {response['answer']}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Erro: {e}")

def main() -> None:
    try:
        iniciar_chat()
    except Exception as e:
        logging.error(e)

if __name__ == "__main__":
    main()
