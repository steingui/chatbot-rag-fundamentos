import os
import random
import logging
from typing import List, Dict

# Fase 1/2: Prompts provocativos elaborados manualmente ou gerados por LLM
PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "curated_prompts.json")

def load_prompts() -> List[str]:
    try:
        import json
        with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Erro ao carregar curated_prompts.json: {e}")
        return ["Qual é a correlação entre as empresas que mais doaram no TSE e os maiores contratos no Portal da Transparência?"]

def get_top_suggestions(limit: int = 4) -> List[Dict]:
    """Fase 1/2: Retorna N iscas curiosas aleatórias (sem contadores)."""
    prompts = load_prompts()
    limit = max(1, min(int(limit), len(prompts)))
    selected = random.sample(prompts, limit)
    # A estrutura atual do frontend esperava Dict com "prompt" e opcional "count" (agora obsoleto)
    return [{"prompt": p} for p in selected]

def record_query(query: str):
    """(Obsoleto) - Função mantida vazia provisoriamente para não quebrar background_tasks do main.py."""
    pass


