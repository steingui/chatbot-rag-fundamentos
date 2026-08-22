from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import re
from typing import Optional

from backend.rag.chat import init_components, get_rag_chain
from backend.api.analytics import get_top_suggestions, record_query

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização lazy — não bloqueia o healthcheck do Render
    logging.info("API iniciada. RAG será carregado na primeira requisição.")
    yield

app = FastAPI(title="Chatbot RAG API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    count: int


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionItem]


@app.get("/suggestions", response_model=SuggestionsResponse)
def suggestions():
    return SuggestionsResponse(suggestions=get_top_suggestions(limit=4))


_rag_initialized = False


def ensure_initialized():
    global _rag_initialized
    if not _rag_initialized:
        logging.info("Inicializando componentes do RAG na primeira requisição...")
        init_components()
        _rag_initialized = True


@app.get("/")
def read_root():
    return {"status": "ok", "message": "API RAG rodando no Render"}


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
    elif "tse_plano" in raw_source or "pdf" in raw_source.lower():
        return SourceObject(
            type="TSE - DivulgaCand",
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
def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    try:
        ensure_initialized()
        background_tasks.add_task(record_query, request.query)
        rag_chain = get_rag_chain(request.session_id, model_name=request.model)
        response = rag_chain.invoke({"question": request.query})
        
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

        return ChatResponse(answer=response["answer"], sources=structured_sources)
    except Exception as e:
        logging.error(f"Erro no chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
