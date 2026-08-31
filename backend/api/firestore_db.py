import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def _get_db():
    try:
        from firebase_admin import firestore
        return firestore.client()
    except Exception as e:
        logger.debug(f"Firestore cliente nao disponivel: {e}")
        return None

def save_chat_message(user_id: str, session_id: str, role: str, content: str, sources: Optional[List[Dict[str, Any]]] = None) -> bool:
    """Salva uma mensagem de chat no Firestore sob users/{user_id}/sessions/{session_id}/messages."""
    db = _get_db()
    if not db or user_id == "anonymous":
        return False

    try:
        doc_ref = db.collection("users").document(user_id).collection("sessions").document(session_id).collection("messages").document()
        doc_ref.set({
            "role": role,
            "content": content,
            "sources": sources or [],
            "timestamp": datetime.utcnow().isoformat()
        })
        # Atualiza a ultima atividade da sessao
        db.collection("users").document(user_id).collection("sessions").document(session_id).set({
            "updated_at": datetime.utcnow().isoformat(),
            "last_message": content[:100]
        }, merge=True)
        return True
    except Exception as e:
        logger.warning(f"Falha ao salvar mensagem no Firestore: {e}")
        return False

def get_session_messages(user_id: str, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Recupera mensagens da sessao do usuario no Firestore."""
    db = _get_db()
    if not db or user_id == "anonymous":
        return []

    try:
        messages_ref = db.collection("users").document(user_id).collection("sessions").document(session_id).collection("messages")
        query = messages_ref.order_by("timestamp").limit(limit)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.warning(f"Falha ao carregar historico do Firestore: {e}")
        return []
