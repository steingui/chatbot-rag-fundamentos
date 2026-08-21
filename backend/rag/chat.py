import os
import logging
import re
from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import Tool
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")

_retriever = None
_llm = None
_session_agents = {}
_session_sources = {}

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
    _retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    _llm = ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openai_api_base=OPENROUTER_BASE,
        max_retries=10,
        temperature=0.2
    )

def _consultar_pinecone(query: str, session_id: str = "default") -> str:
    if _retriever is None:
        return "Erro: retriever não inicializado."
    docs = _retriever.invoke(query)
    if session_id not in _session_sources:
        _session_sources[session_id] = []
    
    formatted_texts = []
    for doc in docs:
        _session_sources[session_id].append(doc)
        src = doc.metadata.get("source", "Desconhecido")
        formatted_texts.append(f"[Fonte: {src}]\n{doc.page_content}")
    
    return "\n\n".join(formatted_texts) if formatted_texts else "Nenhum documento relevante encontrado na base interna."

def _buscar_noticias_web(query: str, session_id: str = "default") -> str:
    try:
        search_tool = DuckDuckGoSearchResults(num_results=5)
        results_str = search_tool.run(query)
        
        urls = re.findall(r'link:\s*(https?://[^\s,]+)', results_str)
        if session_id not in _session_sources:
            _session_sources[session_id] = []
        for url in urls:
            _session_sources[session_id].append(Document(page_content=url, metadata={"source": url}))
            
        return results_str
    except Exception as e:
        logging.error(f"Erro no DuckDuckGo: {e}")
        return "Não foi possível obter notícias recentes da web no momento."

class MultiSourceAgentChain:
    def __init__(self, llm: ChatOpenAI, session_id: str):
        self.llm = llm
        self.session_id = session_id

    def invoke(self, inputs: dict) -> dict:
        question = inputs.get("question", "")
        sources: list[Document] = []
        
        # 1. Recupera documentos da base vetorial (Pinecone)
        pinecone_context = ""
        try:
            if _retriever is not None:
                docs = _retriever.invoke(question)
                formatted = []
                for doc in docs:
                    sources.append(doc)
                    src = doc.metadata.get("source", "Desconhecido")
                    formatted.append(f"[Fonte Base: {src}]\n{doc.page_content}")
                pinecone_context = "\n\n".join(formatted) if formatted else "Nenhum documento encontrado na base interna."
        except Exception as e:
            logging.error(f"Erro ao consultar Pinecone: {e}")
            pinecone_context = "Falha ao consultar a base interna."

        # 2. Recupera fatos recentes da Web (DuckDuckGo)
        web_context = ""
        try:
            search_tool = DuckDuckGoSearchResults(num_results=4)
            web_raw = search_tool.run(question)
            web_context = web_raw
            
            urls = re.findall(r'link:\s*(https?://[^\s,]+)', web_raw)
            for url in urls:
                sources.append(Document(page_content=url, metadata={"source": url}))
        except Exception as e:
            logging.error(f"Erro no DuckDuckGo: {e}")
            web_context = "Notícias recentes da web indisponíveis no momento."

        # 3. Prompt de síntese unificada (Merge de RAG + Web)
        prompt_text = f"""Você é um assistente especialista em política brasileira e análise legislativa.
Sua tarefa é responder à pergunta do usuário SINTETIZANDO E MESCLANDO as informações das duas fontes abaixo (Base Interna e Notícias da Web).

REGRA CRÍTICA:
- Se houver dados em ambas as fontes, funda-os em uma resposta única, coesa e estruturada.
- Se perguntado sobre nomes, listas ou valores específicos e não houver comprovação exata nas fontes, NUNCA invente dados. Diga explicitamente o que foi encontrado.

--- DADOS DA BASE INTERNA (Câmara/TSE/Checagens): ---
{pinecone_context}

--- DADOS RECENTES DA WEB (DuckDuckGo): ---
{web_context}

--- PERGUNTA DO USUÁRIO: ---
{question}

Resposta:"""

        try:
            res = self.llm.invoke(prompt_text)
            answer = res.content if hasattr(res, 'content') else str(res)
        except Exception as e:
            logging.error(f"Erro no LLM: {e}")
            answer = "Não foi possível gerar a resposta no momento."

        return {
            "answer": answer,
            "source_documents": sources
        }

def get_rag_chain(session_id: str = "default"):
    if _llm is None:
        init_components()

    if session_id in _session_agents:
        return _session_agents[session_id]

    chain = MultiSourceAgentChain(_llm, session_id)
    _session_agents[session_id] = chain
    return chain

def iniciar_chat() -> None:
    print("\nAgente Politico RAG + Web conectado. Digite 'sair' para encerrar.")
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
