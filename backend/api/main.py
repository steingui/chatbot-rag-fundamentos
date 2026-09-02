from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
import logging
import os
import re
from typing import Optional

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Depends
from backend.rag.chat import init_components, get_rag_chain
from backend.rag.cache import global_rag_cache
from backend.api.analytics import get_top_suggestions, record_query
from backend.api.guardrails import validate_and_sanitize_query
from backend.api.auth import get_optional_user
from backend.api.firestore_db import save_chat_message

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização lazy — não bloqueia o healthcheck do Render
    logging.info("API iniciada. RAG será carregado na primeira requisição.")
    yield

app = FastAPI(title="Chatbot RAG API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SEC-001: CORS restrito a domínios conhecidos
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "https://rag-eleicoes.web.app,https://rag-eleicoes.firebaseapp.app,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# SEC-003: Security Headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)


# SEC-005: Validação de Origin para endpoints POST (mitiga abuso direto da API)
class OriginCheckMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "POST":
            origin = request.headers.get("origin", "")
            referer = request.headers.get("referer", "")
            is_trusted = any(
                origin.startswith(o) or referer.startswith(o) for o in ALLOWED_ORIGINS
            )
            if not is_trusted and origin:
                logging.warning(f"SEC-005: Origin não confiável bloqueado: {origin}")
                from starlette.responses import JSONResponse
                return JSONResponse(status_code=403, content={"detail": "Origin não autorizado."})
        return await call_next(request)

app.add_middleware(OriginCheckMiddleware)


# SEC-009: Allowlist de modelos para prevenir cache poisoning
ALLOWED_MODELS = {
    "gemini-2.0-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro-002",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "qwen/qwen-2.5-coder-32b-instruct:free"
}


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default="default_session", description="ID da sessão do usuário")
    query: str
    model: Optional[str] = Field(default=None, description="Modelo OpenRouter a ser utilizado")


class SourceObject(BaseModel):
    type: str
    label: str
    url: Optional[str] = None
    raw_file: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceObject] = Field(default_factory=list, description="Lista estruturada de fontes")


class SuggestionItem(BaseModel):
    prompt: str
    count: Optional[int] = Field(default=0)


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionItem]


@app.get("/suggestions", response_model=SuggestionsResponse)
@limiter.limit("60/minute")
def suggestions(request: Request):
    return SuggestionsResponse(suggestions=get_top_suggestions(limit=8))


_rag_initialized = False


def ensure_initialized():
    global _rag_initialized
    if not _rag_initialized:
        logging.info("Inicializando componentes do RAG na primeira requisição...")
        init_components()
        _rag_initialized = True


@app.get("/")
def read_root():
    return {"status": "ok", "message": "API RAG rodando no Cloud Run"}


def parse_source_name(raw_source: str) -> SourceObject:
    if raw_source.startswith("http://") or raw_source.startswith("https://"):
        try:
            domain = raw_source.split("/")[2].replace("www.", "")
        except Exception:
            domain = "web"
        return SourceObject(
            type="Notícia Web (DuckDuckGo)",
            label=f"Web: {domain}",
            url=raw_source,
            raw_file=raw_source
        )
    elif "votacao_" in raw_source:
        match = re.search(r"votacao_(\d+)", raw_source)
        prop_id = match.group(1) if match else ""
        return SourceObject(
            type="Câmara dos Deputados",
            label="Histórico de Votação",
            url=f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={prop_id}" if prop_id else None,
            raw_file=raw_source
        )
    elif "senado" in raw_source.lower():
        return SourceObject(
            type="Senado Federal",
            label="Matéria / Discurso",
            url="https://legis.senado.leg.br/dadosabertos/docs/ui/",
            raw_file=raw_source
        )
    elif "transparencia" in raw_source.lower() or "cgu" in raw_source.lower():
        return SourceObject(
            type="Portal da Transparência (CGU)",
            label="Execução Orçamentária",
            url="https://portaldatransparencia.gov.br/",
            raw_file=raw_source
        )
    elif "lupa" in raw_source.lower() or "aosfatos" in raw_source.lower():
        return SourceObject(
            type="Agência de Fact-Checking",
            label="Checagem de Fatos",
            url="https://lupa.uol.com.br/",
            raw_file=raw_source
        )
    elif "tse_bens" in raw_source:
        return SourceObject(
            type="TSE - DivulgaCand",
            label="Declaração de Bens",
            url="https://divulgacandcontas.tse.jus.br/",
            raw_file=raw_source
        )
    elif "proposicao" in raw_source.lower() or "camara" in raw_source.lower():
        return SourceObject(
            type="Dados Oficiais",
            label="Câmara dos Deputados",
            url="https://www.camara.leg.br/",
            raw_file=raw_source
        )
    elif "plano_governo" in raw_source.lower() or "tse" in raw_source.lower():
        return SourceObject(
            type="Dados Oficiais",
            label="Plano de Governo",
            url="https://divulgacandcontas.tse.jus.br/",
            raw_file=raw_source
        )
    else:
        return SourceObject(
            type="Documento Interno",
            label="Base de Conhecimento",
            url=None,
            raw_file=raw_source
        )


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")
async def chat(request: Request, body: ChatRequest, background_tasks: BackgroundTasks, current_user: Optional[dict] = Depends(get_optional_user)):
    try:
        query = validate_and_sanitize_query(body.query)
        if body.model and body.model not in ALLOWED_MODELS:
            raise HTTPException(status_code=400, detail="Modelo não permitido.")
        
        user_id = current_user.get("uid") if current_user else "anonymous"

        cached = global_rag_cache.get(query, body.model)
        if cached:
            background_tasks.add_task(record_query, query)
            if user_id != "anonymous":
                background_tasks.add_task(save_chat_message, user_id, body.session_id, "user", query)
                background_tasks.add_task(save_chat_message, user_id, body.session_id, "assistant", cached.get("answer", ""), cached.get("sources", []))
            sources = [SourceObject(**s) for s in cached.get("sources", [])]
            return ChatResponse(answer=cached.get("answer", ""), sources=sources)

        ensure_initialized()
        background_tasks.add_task(record_query, query)
        rag_chain = get_rag_chain(body.session_id, model_name=body.model)
        response = rag_chain.invoke({"question": query})
        
        seen_keys = set()
        structured_sources = []
        
        if "source_documents" in response:
            for doc in response["source_documents"]:
                src = doc.metadata.get("source", "Desconhecido")
                source_obj = parse_source_name(src)
                key = (source_obj.label, source_obj.url)
                if key not in seen_keys:
                    seen_keys.add(key)
                    structured_sources.append(source_obj)
        
        sources_dict = [s.model_dump() for s in structured_sources]
        global_rag_cache.set(query, {"answer": response["answer"], "sources": sources_dict}, body.model)
        
        if user_id != "anonymous":
            background_tasks.add_task(save_chat_message, user_id, body.session_id, "user", query)
            background_tasks.add_task(save_chat_message, user_id, body.session_id, "assistant", response["answer"], sources_dict)

        return ChatResponse(answer=response["answer"], sources=structured_sources)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro no chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor. Tente novamente.")


import json
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
@limiter.limit("30/minute")
async def chat_stream(request: Request, body: ChatRequest, background_tasks: BackgroundTasks, current_user: Optional[dict] = Depends(get_optional_user)):
    try:
        query = validate_and_sanitize_query(body.query)
        if body.model and body.model not in ALLOWED_MODELS:
            raise HTTPException(status_code=400, detail="Modelo não permitido.")
        
        user_id = current_user.get("uid") if current_user else "anonymous"
        cached = global_rag_cache.get(query, body.model)
        
        if cached:
            background_tasks.add_task(record_query, query)
            if user_id != "anonymous":
                background_tasks.add_task(save_chat_message, user_id, body.session_id, "user", query)
                background_tasks.add_task(save_chat_message, user_id, body.session_id, "assistant", cached.get("answer", ""), cached.get("sources", []))
            def cached_event_generator():
                payload_src = {"type": "sources", "sources": cached.get("sources", [])}
                yield f"data: {json.dumps(payload_src, ensure_ascii=False)}\n\n"
                payload_tok = {"type": "token", "token": cached.get("answer", "")}
                yield f"data: {json.dumps(payload_tok, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(cached_event_generator(), media_type="text/event-stream")

        ensure_initialized()
        background_tasks.add_task(record_query, query)
        rag_chain = get_rag_chain(body.session_id, model_name=body.model)

        def event_generator():
            try:
                full_tokens = []
                cached_sources = []
                for item in rag_chain.stream({"question": query}):
                    if item.get("type") == "sources":
                        seen_keys = set()
                        structured_sources = []
                        for doc in item.get("source_documents", []):
                            src = doc.metadata.get("source", "Desconhecido")
                            source_obj = parse_source_name(src)
                            key = (source_obj.label, source_obj.url)
                            if key not in seen_keys:
                                seen_keys.add(key)
                                structured_sources.append(source_obj.model_dump())
                        cached_sources = structured_sources
                        payload = {"type": "sources", "sources": structured_sources}
                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    elif item.get("type") == "token":
                        token = item.get("token", "")
                        full_tokens.append(token)
                        payload = {"type": "token", "token": token}
                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                
                final_answer = "".join(full_tokens)
                global_rag_cache.set(query, {"answer": final_answer, "sources": cached_sources}, body.model)
                if user_id != "anonymous":
                    save_chat_message(user_id, body.session_id, "user", query)
                    save_chat_message(user_id, body.session_id, "assistant", final_answer, cached_sources)
                yield "data: [DONE]\n\n"
            except Exception as stream_err:
                logging.error(f"Erro no event_generator: {stream_err}")
                err_payload = {"type": "token", "token": f"\n[Erro no processamento: {stream_err}]"}
                yield f"data: {json.dumps(err_payload, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro no chat_stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor. Tente novamente.")
