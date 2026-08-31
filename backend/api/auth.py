import os
import json
import logging
from typing import Optional
from fastapi import Request, Header, HTTPException, status
import firebase_admin
from firebase_admin import credentials, auth

logger = logging.getLogger(__name__)

_firebase_initialized = False

def init_firebase():
    global _firebase_initialized
    if _firebase_initialized or firebase_admin._apps:
        _firebase_initialized = True
        return

    try:
        service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH", "firebase-service-account.json")
        service_account_json_env = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info(f"Firebase Admin SDK inicializado via arquivo: {service_account_path}")
            _firebase_initialized = True
        elif service_account_json_env:
            cred_dict = json.loads(service_account_json_env)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK inicializado via variavel de ambiente JSON")
            _firebase_initialized = True
        else:
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK inicializado via default credentials")
            _firebase_initialized = True
    except Exception as e:
        logger.warning(f"Aviso: Firebase Admin SDK nao pode ser inicializado (desativado): {e}")

# Inicializa ao carregar o modulo
init_firebase()

async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Retorna os dados do usuario se o token Bearer JWT do Firebase for valido.
    Se nao for fornecido token, retorna None para compatibilidade web/anonimo."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split("Bearer ")[1].strip()
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name")
        }
    except Exception as e:
        logger.warning(f"Token JWT do Firebase invalido ou expirado: {e}")
        return None

async def get_required_user(authorization: Optional[str] = Header(None)) -> dict:
    """Exige autenticacao via Bearer JWT do Firebase."""
    user = await get_optional_user(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação requerida. Token Bearer inválido ou ausente."
        )
    return user
