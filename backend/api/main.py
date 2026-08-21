from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import logging
from typing import Optional

from backend.rag.chat import init_components, get_rag_chain

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização lazy — não bloqueia o healthcheck do Render
    logging.info("API iniciada. RAG será carregado na primeira requisição.")
    yield

app = FastAPI(title="Chatbot RAG API", version="1.0.0", lifespan=lifespan)

import re

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default="default_session", description="ID da sessão do usuário")
    query: str

class SourceObject(BaseModel):
    type: str
    label: str
    url: Optional[str] = None
    raw_file: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceObject] = Field(default_factory=list, description="Lista estruturada de fontes")

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
    if "votacao_" in raw_source:
        # Puxa o ID da proposicao (ex: 2618177) do nome do arquivo
        match = re.search(r"votacao_(\d+)", raw_source)
        prop_id = match.group(1) if match else ""
        return SourceObject(
            type="Câmara dos Deputados",
            label="Histórico de Votação",
            url=f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={prop_id}" if prop_id else None,
            raw_file=raw_source
        )
    elif "lupa" in raw_source.lower() or "aosfatos" in raw_source.lower():
        return SourceObject(
            type="Agência de Fact-Checking",
            label="Checagem de Fatos",
            url="https://lupa.uol.com.br/", # Mock estático para frontend
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
def chat(request: ChatRequest):
    try:
        ensure_initialized()
        rag_chain = get_rag_chain(request.session_id)
        response = rag_chain.invoke({"question": request.query})
        
        seen_files = set()
        structured_sources = []
        
        if "source_documents" in response:
            for doc in response["source_documents"]:
                src = doc.metadata.get("source", "Desconhecido")
                if src not in seen_files:
                    seen_files.add(src)
                    structured_sources.append(parse_source_name(src))

        return ChatResponse(answer=response["answer"], sources=structured_sources)
    except Exception as e:
        logging.error(f"Erro no chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
