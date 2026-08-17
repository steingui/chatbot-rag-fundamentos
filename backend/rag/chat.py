import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

DB_DIR = "chroma_db"

def main():
    if not os.path.exists(DB_DIR):
        print("Vector DB não encontrado. Execute 'python ingest.py' primeiro.")
        return

    print("Carregando Vector DB...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    print("Inicializando modelo via OpenRouter...")
    llm = ChatOpenAI(
        model="meta-llama/llama-3-8b-instruct:free",
        openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1"
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
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    print("\nChatbot RAG inicializado. Digite 'sair' para encerrar.")
    while True:
        user_input = input("\nVocê: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            break

        response = rag_chain.invoke({"input": user_input})
        print(f"\nBot: {response['answer']}")

if __name__ == "__main__":
    main()
