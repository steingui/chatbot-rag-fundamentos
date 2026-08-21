from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import logging
from typing import Optional

from backend.rag.chat import init_components, get_rag_chain

app = FastAPI(title="Chatbot RAG API", version="1.0.0")

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default="default_session", description="ID da sessão do usuário")
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list, description="Lista de fontes (arquivos) consultadas")

# Instancia a chain no startup
try:
    init_components()
    logging.info("Componentes do RAG carregados com sucesso na API.")
except Exception as e:
    logging.error(f"Erro ao inicializar RAG: {e}")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API RAG rodando no Render"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        rag_chain = get_rag_chain(request.session_id)
        response = rag_chain.invoke({"question": request.query})
        
        sources = []
        if "source_documents" in response:
            for doc in response["source_documents"]:
                src = doc.metadata.get("source", "Desconhecido")
                if src not in sources:
                    sources.append(src)

        return ChatResponse(answer=response["answer"], sources=sources)
    except Exception as e:
        logging.error(f"Erro no chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
