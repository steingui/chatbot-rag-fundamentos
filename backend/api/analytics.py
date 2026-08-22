import os
import random
import logging
from typing import List, Dict

# Fase 1: Prompts provocativos elaborados manualmente
CURATED_PROMPTS = [
    "Qual é a correlação entre as empresas que mais doaram no TSE e os maiores contratos no Portal da Transparência?",
    "Liste os parlamentares que mais mudaram de voto em pautas ambientais nos últimos 4 anos.",
    "Quais são as emendas parlamentares mais atípicas pagas no último mês?",
    "Quais senadores mais utilizaram a cota parlamentar (CEAPS) nos últimos 6 meses?",
    "Houve alguma ligação entre as votações recentes de desoneração fiscal e o plano de governo eleito?",
    "Quais propostas na Câmara dos Deputados mais divergem dos dados de execução orçamentária do Portal da Transparência?",
    "O que diz a base de fact-checking sobre fraudes eleitorais recentes e as falas na CPI das urnas?",
    "Há casos recentes de empresas recém-criadas recebendo grandes repasses da União via CGU?"
]

def get_top_suggestions(limit: int = 4) -> List[Dict]:
    """Fase 1: Retorna N iscas curiosas aleatórias (sem contadores)."""
    limit = max(1, min(int(limit), len(CURATED_PROMPTS)))
    selected = random.sample(CURATED_PROMPTS, limit)
    # A estrutura atual do frontend esperava Dict com "prompt" e opcional "count" (agora obsoleto)
    return [{"prompt": p} for p in selected]

def record_query(query: str):
    """(Obsoleto) - Função mantida vazia provisoriamente para não quebrar background_tasks do main.py."""
    pass

def _canonizar_via_llm(raw_query: str) -> str:
    """Utiliza LLM leve para formatar uma nova pergunta no padrão perfeito de título/sugestão."""
    try:
        from langchain_openai import ChatOpenAI
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            return raw_query.strip().capitalize()

        llm = ChatOpenAI(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_retries=1,
            temperature=0.1
        )
        prompt = f"""Reescreva a pergunta a seguir em uma única frase elegante, direta e gramaticalmente perfeita em português para servir de título de sugestão de busca (iniciando com maiúscula e terminando adequadamente com ponto ou interrogação). Retorne APENAS o texto formatado, sem aspas nem explicações.

Pergunta original: {raw_query}

Resposta:"""
        res = llm.invoke(prompt)
        text = res.content.strip().strip('"').strip("'") if hasattr(res, 'content') else str(res).strip()
        return text if text else raw_query.strip().capitalize()
    except Exception as e:
        logging.warning(f"Aviso na canonização via LLM: {e}")
        return raw_query.strip().capitalize()


def record_query(raw_query: str):
    """Registra uma consulta utilizando a estratégia Híbrida (Fuzzy Match + LLM Fallback)."""
    query_clean = raw_query.strip()
    if len(query_clean) < 5:
        return  # Ignora buscas muito curtas

    try:
        init_analytics_db()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, canonical_prompt, count FROM query_stats")
            existing_rows = cursor.fetchall()

            best_match_id = None
            best_ratio = 0.0

            # 1. Tenta Fuzzy Match (Similaridade Léxica > 70%)
            for row in existing_rows:
                ratio = difflib.SequenceMatcher(None, query_clean.lower(), row["canonical_prompt"].lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match_id = row["id"]

            if best_ratio >= 0.68 and best_match_id is not None:
                # Incrementa contagem no match existente
                cursor.execute(
                    "UPDATE query_stats SET count = count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (best_match_id,)
                )
                conn.commit()
                return

            # 2. Se não houver match próximo, canoniza via LLM e insere como nova sugestão
            canonical_text = _canonizar_via_llm(query_clean)
            
            cursor.execute(
                "INSERT INTO query_stats (canonical_prompt, count) VALUES (?, 1) ON CONFLICT(canonical_prompt) DO UPDATE SET count = count + 1, updated_at = CURRENT_TIMESTAMP",
                (canonical_text,)
            )
            conn.commit()
    except Exception as e:
        logging.error(f"Erro ao registrar query no analytics SQLite: {e}")
