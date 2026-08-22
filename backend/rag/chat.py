import os
import logging
import re
from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
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

    logging.info(f"Conectando ao Pinecone (Index: {INDEX_NAME}) e ao LLM com resiliência a 429...")
    
    embeddings = HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        huggingfacehub_api_token=os.environ.get("HF_TOKEN")
    )
    vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    _retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    api_key = os.environ.get("OPENROUTER_API_KEY", "")

    # LLM Principal + Fallbacks para contornar Rate Limit (HTTP 429) no OpenRouter Free Tier
    primary_llm = ChatOpenAI(
        model="nvidia/nemotron-3-nano-30b-a3b:free",
        openai_api_key=api_key,
        openai_api_base=OPENROUTER_BASE,
        max_retries=3,
        temperature=0.2
    )

    fallback_1 = ChatOpenAI(
        model="meta-llama/llama-3.3-70b-instruct:free",
        openai_api_key=api_key,
        openai_api_base=OPENROUTER_BASE,
        max_retries=3,
        temperature=0.2
    )

    fallback_2 = ChatOpenAI(
        model="deepseek/deepseek-r1:free",
        openai_api_key=api_key,
        openai_api_base=OPENROUTER_BASE,
        max_retries=3,
        temperature=0.2
    )

    _llm = primary_llm.with_fallbacks([fallback_1, fallback_2])


def _buscar_noticias_web(query: str, session_id: str = "default") -> tuple[str, list[Document]]:
    """Recupera notícias e dados da web diretamente via DDGS.text (sem endpoints quebrados da wikipedia)."""
    sources = []
    formatted_results = []
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
            for item in results:
                title = item.get("title", "")
                href = item.get("href", "")
                snippet = item.get("body", "")
                if href:
                    sources.append(Document(page_content=f"{title}: {snippet}", metadata={"source": href}))
                    formatted_results.append(f"[Título: {title} | Fonte Web: {href}]\n{snippet}")

        results_str = "\n\n".join(formatted_results) if formatted_results else "Nenhuma notícia relevante encontrada na web."
        return results_str, sources
    except Exception as e:
        logging.warning(f"Aviso no DuckDuckGo (Web Search): {e}")
        return "Notícias recentes da web indisponíveis no momento.", []


class MultiSourceAgentChain:
    def __init__(self, llm, session_id: str):
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

        # 2. Recupera fatos recentes da Web (DuckDuckGo direto)
        web_context, web_sources = _buscar_noticias_web(question, self.session_id)
        sources.extend(web_sources)

        # 3. Prompt de síntese unificada (Merge de RAG + Web)
        prompt_text = f"""Você é um assistente especialista em política brasileira e análise legislativa.
Sua tarefa é responder à pergunta do usuário SINTETIZANDO E MESCLANDO as informações das duas fontes abaixo (Base Interna e Notícias da Web).

REGRA CRÍTICA:
- Se houver dados em ambas as fontes, funda-os em uma resposta única, coesa e estruturada.
- Se perguntado sobre nomes, listas ou valores específicos e não houver comprovação exata nas fontes, NUNCA invente dados. Diga explicitamente o que foi encontrado.

--- DADOS DA BASE INTERNA (Câmara/Senado/TSE/CGU/Checagens): ---
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
            logging.error(f"Erro ao chamar LLM: {e}")
            answer = "Não foi possível gerar a resposta no momento devido a instabilidade temporária no serviço de LLM."

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
    print("\nAgente Político RAG + Web conectado. Digite 'sair' para encerrar.")
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
