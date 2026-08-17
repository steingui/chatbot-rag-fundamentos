from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

from backend.rag.chat import build_rag_chain

app = FastAPI(title="Chatbot RAG API", version="1.0.0")

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

# Instancia a chain no startup
try:
    rag_chain = build_rag_chain()
    logging.info("RAG Chain carregada com sucesso na API.")
except Exception as e:
    logging.error(f"Erro ao carregar RAG Chain: {e}")
    rag_chain = None

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API RAG rodando no Hugging Face Spaces"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not rag_chain:
        raise HTTPException(status_code=500, detail="RAG Chain não está disponível. Verifique as chaves de API.")
    
    try:
        response = rag_chain.invoke({"question": request.query})
        return ChatResponse(answer=response["answer"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
