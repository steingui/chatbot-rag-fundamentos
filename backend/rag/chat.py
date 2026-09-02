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


def init_components():
    global _retriever, _llm
    if not os.environ.get("PINECONE_API_KEY"):
        raise ValueError("PINECONE_API_KEY não configurada no .env!")

    logging.info(f"Conectando ao Pinecone (Index: {INDEX_NAME}) e ao LLM com resiliência a 429...")
    
    from pinecone import Pinecone
    from langchain_community.retrievers import PineconeHybridSearchRetriever
    from backend.rag.sparse_encoder import FastBM25Encoder

    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(INDEX_NAME)

    embeddings = HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        huggingfacehub_api_token=os.environ.get("HF_TOKEN")
    )
    
    # Encoder Lexico Leve (evita OOM no Render)
    bm25_encoder = FastBM25Encoder()

    from langchain_pinecone import PineconeRerank
    from langchain_classic.retrievers import ContextualCompressionRetriever

    base_retriever = PineconeHybridSearchRetriever(
        embeddings=embeddings,
        sparse_encoder=bm25_encoder,
        index=index,
        top_k=30
    )

    # Reranker Nativo (Pinecone Inference) para filtrar ruído e mitigar alucinação
    reranker = PineconeRerank(
        model="bge-reranker-v2-m3",
        pinecone_api_key=os.environ.get("PINECONE_API_KEY"),
        top_n=5
    )

    _retriever = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=base_retriever
    )

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    google_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    api_key = os.environ.get("OPENROUTER_API_KEY", "")

    fallbacks = []
    if google_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            gemini_candidates = ["gemini-2.0-flash", "gemini-1.5-flash-001", "gemini-1.5-pro-001", "gemini-1.5-flash-8b"]
            for m in gemini_candidates:
                try:
                    fallbacks.append(
                        ChatGoogleGenerativeAI(
                            model=m,
                            google_api_key=google_key,
                            temperature=0.2,
                            max_retries=2
                        )
                    )
                except Exception:
                    pass
        except Exception as e:
            logging.warning(f"Falha ao criar fallbacks Gemini: {e}")

    if api_key:
        fallbacks.extend([
            ChatOpenAI(
                model="meta-llama/llama-3.3-70b-instruct:free",
                openai_api_key=api_key,
                openai_api_base=OPENROUTER_BASE,
                max_retries=2,
                temperature=0.2
            ),
            ChatOpenAI(
                model="deepseek/deepseek-r1-distill-llama-70b:free",
                openai_api_key=api_key,
                openai_api_base=OPENROUTER_BASE,
                max_retries=2,
                temperature=0.2
            )
        ])

    if google_key and fallbacks:
        try:
            primary_llm = fallbacks[0]
            rest_fallbacks = fallbacks[1:]
            _llm = primary_llm.with_fallbacks(rest_fallbacks) if rest_fallbacks else primary_llm
        except Exception as e:
            logging.warning(f"Falha ao carregar Gemini nativo: {e}")
            _llm = fallbacks[0] if fallbacks else None
    elif fallbacks:
        _llm = fallbacks[0].with_fallbacks(fallbacks[1:]) if len(fallbacks) > 1 else fallbacks[0]
    else:
        raise ValueError("Nenhuma chave de API configurada (GEMINI_API_KEY ou OPENROUTER_API_KEY)")


def _clean_url(url: str) -> str:
    """Remove parâmetros de rastreamento (UTM, etc.) mantendo a URL limpa."""
    return re.sub(r'(\?|&)utm_[^&]+', '', url).rstrip('?&')


def _buscar_noticias_web(query: str, session_id: str = "default") -> tuple[str, list[Document]]:
    """Recupera notícias e dados da web via DDGS (Text + News fallback) com timeout de 5s e região Brasil."""
    sources = []
    formatted_results = []
    
    try:
        from ddgs import DDGS
        results = []
        
        # Estratégia 1: Busca de texto otimizada para o Brasil
        with DDGS(timeout=5) as ddgs:
            try:
                results = list(ddgs.text(query, region="br-pt", max_results=5))
            except Exception as txt_err:
                logging.debug(f"Falha no modo texto DDGS, tentando aba notícias: {txt_err}")
                
            # Estratégia 2: Fallback para Notícias se a busca textual não trouxer resultados
            if not results:
                try:
                    results = list(ddgs.news(query, region="br-pt", max_results=5))
                except Exception as news_err:
                    logging.debug(f"Falha no modo notícias DDGS: {news_err}")

            # Processamento e deduplicação
            seen_urls = set()
            for item in results:
                title = item.get("title", "").strip()
                href = _clean_url(item.get("href", item.get("url", "")).strip())
                snippet = item.get("body", item.get("excerpt", "")).strip()
                
                if href and href not in seen_urls:
                    seen_urls.add(href)
                    sources.append(Document(page_content=f"{title}: {snippet}", metadata={"source": href}))
                    formatted_results.append(f"[Título: {title} | Fonte Web: {href}]\n{snippet}")

        results_str = "\n\n".join(formatted_results) if formatted_results else "Nenhuma notícia relevante encontrada na web."
        return results_str, sources

    except Exception as e:
        logging.warning(f"Aviso na busca Web (DDGS): {e}")
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

        # 2. Recupera fatos recentes da Web (DDGS BR com fallback)
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

--- DADOS RECENTES DA WEB (DuckDuckGo BR): ---
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

    def stream(self, inputs: dict):
        question = inputs.get("question", "")
        pinecone_docs = _retriever.invoke(question) if _retriever else []
        pinecone_context = "\n\n".join([d.page_content for d in pinecone_docs]) if pinecone_docs else "Nenhum documento interno relevante encontrado."
        sources = list(pinecone_docs)

        web_context, web_sources = _buscar_noticias_web(question, self.session_id)
        sources.extend(web_sources)

        prompt_text = f"""Você é um assistente especialista em política brasileira e análise legislativa.
Sua tarefa é responder à pergunta do usuário SINTETIZANDO E MESCLANDO as informações das duas fontes abaixo (Base Interna e Notícias da Web).

REGRA CRÍTICA:
- Se houver dados em ambas as fontes, funda-os em uma resposta única, coesa e estruturada.
- Se perguntado sobre nomes, listas ou valores específicos e não houver comprovação exata nas fontes, NUNCA invente dados. Diga explicitamente o que foi encontrado.

--- DADOS DA BASE INTERNA (Câmara/Senado/TSE/CGU/Checagens): ---
{pinecone_context}

--- DADOS RECENTES DA WEB (DuckDuckGo BR): ---
{web_context}

--- PERGUNTA DO USUÁRIO: ---
{question}

Resposta:"""

        yield {"type": "sources", "source_documents": sources}

        try:
            for chunk in self.llm.stream(prompt_text):
                text = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if text:
                    yield {"type": "token", "token": text}
        except Exception as e:
            logging.error(f"Erro no streaming LLM: {e}")
            yield {"type": "token", "token": "Não foi possível gerar a resposta completa devido a instabilidade temporária."}



def get_rag_chain(session_id: str = "default", model_name: str = None):
    if _llm is None:
        init_components()

    if model_name:
        google_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if (model_name.startswith("gemini") or "gemini" in model_name) and google_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                gemini_fallbacks = [
                    ChatGoogleGenerativeAI(model=m, google_api_key=google_key, temperature=0.2, max_retries=2)
                    for m in ["gemini-2.0-flash", "gemini-1.5-flash-001", "gemini-1.5-pro-001"]
                    if m != model_name
                ]
                primary_custom = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=google_key,
                    temperature=0.2,
                    max_retries=2
                )
                fallback_list = gemini_fallbacks + ([_llm] if _llm else [])
                custom_llm = primary_custom.with_fallbacks(fallback_list)
                return MultiSourceAgentChain(custom_llm, session_id)
            except Exception as e:
                logging.warning(f"Falha ao instanciar Gemini {model_name} nativo: {e}")

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        openrouter_model = f"google/{model_name}" if (model_name.startswith("gemini") and "/" not in model_name) else model_name
        if _llm:
            custom_llm = ChatOpenAI(
                model=openrouter_model,
                openai_api_key=api_key or "sk-dummy",
                openai_api_base=OPENROUTER_BASE,
                max_retries=2,
                temperature=0.2
            ).with_fallbacks([_llm])
        else:
            custom_llm = ChatOpenAI(
                model=openrouter_model,
                openai_api_key=api_key or "sk-dummy",
                openai_api_base=OPENROUTER_BASE,
                max_retries=2,
                temperature=0.2
            )
        return MultiSourceAgentChain(custom_llm, session_id)

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
