import os
import logging
import re
from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

from backend.rag.context_window import (
    build_context_window,
    count_tokens,
    format_history,
    max_input_tokens_for_model,
)
from backend.rag.semantic_router import Route, SemanticRouter
from backend.rag.jev_client import CHECK_CONTRADICTED, CHECK_INSUFFICIENT, CHECK_SUPPORTED, jev_check, jev_noul

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")

_retriever = None
_llm = None
_session_agents = {}
_router = SemanticRouter()


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

    fallbacks = []
    if google_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            gemini_candidates = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-pro-latest", "gemini-2.5-flash"]
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


def _extract_text(content_obj) -> str:
    """Extrai texto de respostas que podem vir como string ou lista de blocos (LangChain Gemini 3.x/2.5)."""
    if isinstance(content_obj, str):
        return content_obj
    if isinstance(content_obj, list):
        parts = []
        for item in content_obj:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content_obj) if content_obj is not None else ""


_SYNTHESIS_SYSTEM_PROMPT = """Você é um assistente especialista em política brasileira e análise legislativa.
Sua tarefa é responder à pergunta do usuário aplicando SÍNTESE HIERÁRQUICA, isolando o contexto factual interno dos resultados web secundários.

HIERARQUIA DE CONFIANÇA (obrigatória):
1. FONTE PRIMÁRIA — BASE INTERNA (Câmara/Senado/TSE/CGU/Checagens): fonte factual canônica e verificada. Toda afirmação sobre nomes, listas, valores, votações ou datas DEVE ser ancorada aqui.
2. FONTE SECUNDÁRIA — RESULTADOS WEB (DuckDuckGo BR): complemento de atualidade/contexto. NUNCA substitui, contradiz ou sobrescreve a base interna.

REGRAS CRÍTICAS:
- Isole o contexto factual interno: trate os dados da BASE INTERNA como verdade canônica, sem misturar com o ruído da web.
- Use a web apenas como enriquecimento secundário (recência/contexto), explicitando sempre que a informação vem da web.
- Em caso de conflito entre as fontes, prevaleça SEMPRE a BASE INTERNA e sinalize a divergência.
- Se nomes, listas ou valores específicos não tiverem comprovação exata na BASE INTERNA, NUNCA invente dados. Diga explicitamente o que foi encontrado.
- Se a BASE INTERNA não trouxer dados, responda com a web deixando claro que é informação secundária não verificada.
"""


NOT_FOUND_ANSWER = "Não encontrei informação suficiente na base interna para responder com segurança."

# G3 — Limiar de relevância no rerank: mantém apenas trechos com noul >= limiar.
RERANK_NOUL_THRESHOLD = 0.5

# G4 — Limiar do gate de web search: pergunta exige informação recente/web?
WEB_GATE_NOUL_THRESHOLD = 0.5


def _filter_relevant_docs(question: str, docs: list[Document]) -> list[Document]:
    """Filtra documentos rerankeados por relevância mecânica (noul por trecho).

    Cada documento é julgado individualmente ("este trecho responde à
    pergunta?"). ``None``/falha do Jev ⇒ mantém o documento (o pipeline nunca
    quebra por indisponibilidade do Jev).
    """
    kept: list[Document] = []
    for doc in docs:
        trecho = (doc.page_content or "").strip()
        if not trecho:
            continue
        noul = jev_noul(
            instructions="Does this passage answer the user's question?",
            state={"pergunta": question, "trecho": trecho},
        )
        if noul is None or noul >= RERANK_NOUL_THRESHOLD:
            kept.append(doc)
    return kept


def _needs_web_search(question: str) -> bool:
    """Gate mecânico de web search (G4): a pergunta exige informação recente?

    ``noul`` baixo ("esta pergunta exige informação recente/notícias?") ⇒
    ``False`` — pula DDGS e vai só de Pinecone. ``None``/falha do Jev ⇒
    ``True`` (comportamento atual: web dispara sempre). O pipeline nunca perde
    recência por indisponibilidade do Jev.
    """
    noul = jev_noul(
        instructions="Does this question require recent information or news?",
        state={"pergunta": question},
    )
    return noul is None or noul >= WEB_GATE_NOUL_THRESHOLD


def _answerable(pinecone_context: str, question: str) -> bool:
    """Gate mecânico anti-alucinação (G2): a base interna sustenta a pergunta?

    ``False`` quando a base está vazia ou o Jev julga a evidência insuficiente
    ou contraditória. ``None``/falha do Jev ⇒ ``True`` (comportamento atual).
    """
    if not pinecone_context.strip() or pinecone_context.startswith(("Nenhum documento", "Falha ao consultar")):
        return False
    verdict = jev_check(claim=question, evidence=pinecone_context, state={"pergunta": question})
    if verdict is None:
        return True
    return verdict not in (CHECK_INSUFFICIENT, CHECK_CONTRADICTED)


def _synthesis_evidence(pinecone_context: str, web_context: str) -> str:
    """Evidência combinada (base interna + web) usada para checar a resposta final.

    A síntese hierárquica responde com as duas fontes, então o pós-check deve
    julgar a resposta contra o mesmo material que a gerou — não só contra a base.
    """
    partes = []
    if pinecone_context.strip() and not pinecone_context.startswith(("Nenhum documento", "Falha ao consultar")):
        partes.append(f"[BASE INTERNA]\n{pinecone_context}")
    if web_context.strip():
        partes.append(f"[WEB]\n{web_context}")
    return "\n\n".join(partes)


def _web_conflicts_with_base(pinecone_context: str, web_context: str, question: str) -> bool:
    """Gate mecânico de conflito (G5): a fonte web contradiz a base interna?

    Só dispara quando ambas as fontes existem. ``None``/falha do Jev ou veredito
    diferente de ``supported`` ⇒ ``False`` (resolução por instrução no prompt,
    comportamento atual). Nunca bloqueia o pipeline por indisponibilidade do Jev.
    """
    if not web_context.strip():
        return False
    if not pinecone_context.strip() or pinecone_context.startswith(("Nenhum documento", "Falha ao consultar")):
        return False
    evidence = _synthesis_evidence(pinecone_context, web_context)
    verdict = jev_check(
        claim="A fonte web contradiz a base interna.",
        evidence=evidence,
        state={"pergunta": question},
    )
    return verdict == CHECK_SUPPORTED


def _post_check_ok(answer: str, evidence: str, question: str) -> bool:
    """Pós-geração (G2): a resposta gerada é sustentada pelas evidências usadas?

    Só contradição explícita derruba a resposta — se o Jev falhar (``None``) ou
    julgar ``insufficient`` (evidência fraca, sem refutação), mantém o
    comportamento atual. Sem evidência, não há o que checar.
    """
    if not evidence.strip():
        return True
    verdict = jev_check(claim=answer, evidence=evidence, state={"pergunta": question})
    return verdict != CHECK_CONTRADICTED


def _build_synthesis_prompt(
    pinecone_context: str,
    web_context: str,
    question: str,
    history_text: str = "",
    web_conflict: bool = False,
) -> str:
    """Monta o prompt de síntese hierárquica: base factual interna (primária) isolada dos resultados web (secundários)."""
    history_block = (
        f"\n--- HISTÓRICO RECENTE DA CONVERSA (janela dinâmica): ---\n{history_text}\n"
        if history_text
        else ""
    )
    conflict_block = (
        "\n--- ALERTA DE CONFLITO (mecânico): a fonte web contradiz a base interna. "
        "PRIORIZE a base interna, ignore a divergência da web e cite a divergência explicitamente na resposta. ---"
        if web_conflict
        else ""
    )
    return f"""{_SYNTHESIS_SYSTEM_PROMPT}{history_block}
--- [FONTE PRIMÁRIA] DADOS DA BASE INTERNA (Câmara/Senado/TSE/CGU/Checagens): ---
{pinecone_context}

--- [FONTE SECUNDÁRIA] RESULTADOS WEB (DuckDuckGo BR): ---
{web_context}
{conflict_block}
--- PERGUNTA DO USUÁRIO: ---
{question}

Resposta:"""


class MultiSourceAgentChain:
    def __init__(self, llm, session_id: str, model_name: str = None):
        self.llm = llm
        self.session_id = session_id
        self.model_name = model_name

    def _build_history_block(self, question: str, inputs: dict) -> str:
        """Janela de contexto dinâmica: mantém o histórico recente que cabe no
        orçamento exato de tokens de entrada do modelo (descartando o antigo)."""
        history = inputs.get("history") or []
        if not history:
            return ""

        budget = max_input_tokens_for_model(self.model_name)
        fixed = count_tokens(_SYNTHESIS_SYSTEM_PROMPT) + count_tokens(question)
        history_budget = max(0, budget - fixed)
        windowed = build_context_window(history, history_budget)
        return format_history(windowed)

    def invoke(self, inputs: dict) -> dict:
        question = inputs.get("question", "")
        sources: list[Document] = []
        route = _router.route(question)
        pinecone_context = ""
        web_context = ""

        # 1. Rota RAG: recupera a base vetorial (Pinecone) como fonte primária.
        if route == Route.RAG:
            try:
                if _retriever is not None:
                    docs = _filter_relevant_docs(question, _retriever.invoke(question))
                    formatted = []
                    for doc in docs:
                        sources.append(doc)
                        src = doc.metadata.get("source", "Desconhecido")
                        formatted.append(f"[Fonte Base: {src}]\n{doc.page_content}")
                    pinecone_context = "\n\n".join(formatted) if formatted else "Nenhum documento encontrado na base interna."
            except Exception as e:
                logging.error(f"Erro ao consultar Pinecone: {e}")
                pinecone_context = "Falha ao consultar a base interna."

        # 2. Rota WEB (explícita) sempre aciona DDGS; rota RAG só aciona quando o
        #    gate mecânico (G4) julga que a pergunta exige informação recente.
        if route == Route.WEB or (route == Route.RAG and _needs_web_search(question)):
            web_context, web_sources = _buscar_noticias_web(question, self.session_id)
            sources.extend(web_sources)

        # 3. Gate mecânico anti-alucinação (G2/R3): base insuficiente ⇒ não gera.
        if route == Route.RAG and not _answerable(pinecone_context, question):
            return {"answer": NOT_FOUND_ANSWER, "source_documents": sources}

        # 4. Janela de contexto dinâmica: histórico recente podado por tokens exatos
        history_text = self._build_history_block(question, inputs)

        # 5. Prompt de síntese hierárquica (base factual interna vs. web secundária)
        web_conflict = _web_conflicts_with_base(pinecone_context, web_context, question)
        prompt_text = _build_synthesis_prompt(pinecone_context, web_context, question, history_text, web_conflict)

        try:
            res = self.llm.invoke(prompt_text)
            raw_content = res.content if hasattr(res, 'content') else str(res)
            answer = _extract_text(raw_content)
        except Exception as e:
            logging.error(f"Erro ao chamar LLM: {e}")
            answer = "Não foi possível gerar a resposta no momento devido a instabilidade temporária no serviço de LLM."

        # 6. Pós-geração: verificação mecânica da resposta contra a evidência
        #    que a gerou (base interna + web), espelhando a síntese hierárquica.
        if not _post_check_ok(answer, _synthesis_evidence(pinecone_context, web_context), question):
            answer = NOT_FOUND_ANSWER

        return {
            "answer": answer,
            "source_documents": sources
        }

    def stream(self, inputs: dict):
        question = inputs.get("question", "")
        route = _router.route(question)
        pinecone_docs = _retriever.invoke(question) if (_retriever and route == Route.RAG) else []
        pinecone_context = "\n\n".join([d.page_content for d in pinecone_docs]) if pinecone_docs else "Nenhum documento interno relevante encontrado."
        sources = list(pinecone_docs)

        web_context, web_sources = (
            _buscar_noticias_web(question, self.session_id)
            if route == Route.WEB or (route == Route.RAG and _needs_web_search(question))
            else ("", [])
        )
        sources.extend(web_sources)

        # Gate mecânico anti-alucinação (G2/R3): base insuficiente ⇒ não gera.
        if route == Route.RAG and not _answerable(pinecone_context, question):
            yield {"type": "sources", "source_documents": sources}
            yield {"type": "token", "token": NOT_FOUND_ANSWER}
            return

        history_text = self._build_history_block(question, inputs)
        prompt_text = _build_synthesis_prompt(pinecone_context, web_context, question, history_text)

        yield {"type": "sources", "source_documents": sources}

        try:
            for chunk in self.llm.stream(prompt_text):
                raw_chunk = chunk.content if hasattr(chunk, 'content') else str(chunk)
                text = _extract_text(raw_chunk)
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
                    for m in ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-pro-latest", "gemini-2.5-flash"]
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
                return MultiSourceAgentChain(custom_llm, session_id, model_name)
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
        return MultiSourceAgentChain(custom_llm, session_id, model_name)

    if session_id in _session_agents:
        return _session_agents[session_id]

    chain = MultiSourceAgentChain(_llm, session_id)
    _session_agents[session_id] = chain
    return chain


