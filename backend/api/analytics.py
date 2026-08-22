import os
import sqlite3
import logging
import difflib
from typing import List, Dict

DB_PATH = os.environ.get("ANALYTICS_DB_PATH", os.path.join(os.path.dirname(__file__), "analytics.db"))

INITIAL_SEEDS = [
    ("Quais senadores mais utilizaram a cota parlamentar (CEAPS)?", 32, "senado"),
    ("Qual o resultado da votação 2580259-24 na Câmara dos Deputados?", 28, "camara"),
    ("Quais os gastos da senadora Damares Alves na cota CEAPS?", 25, "senado"),
    ("O que diz a checagem sobre o golpe da lista de CPFs com indenização de R$ 5 mil?", 21, "fact-checking"),
    ("Quais os detalhes da execução orçamentária da Emenda PIX nº 202581000001?", 19, "transparencia"),
    ("Como votaram os senadores na votação do PLP 204 no Senado?", 16, "senado"),
    ("Quais senadores tiveram reembolso de despesas de consumo no Senado em 2025?", 14, "senado"),
    ("Como o deputado Carlos Zarattini votou na votação 2580259-24?", 12, "camara"),
]


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_analytics_db():
    """Inicializa a tabela sqlite e popula seeds iniciais se o banco tiver menos que as sementes padrão."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_prompt TEXT UNIQUE NOT NULL,
                count INTEGER DEFAULT 1,
                category TEXT DEFAULT 'geral',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Popula ou completa sementes iniciais se faltarem itens
        for prompt, count, category in INITIAL_SEEDS:
            cursor.execute(
                "INSERT INTO query_stats (canonical_prompt, count, category) VALUES (?, ?, ?) ON CONFLICT(canonical_prompt) DO NOTHING",
                (prompt, count, category)
            )
        conn.commit()


def get_top_suggestions(limit: int = 8) -> List[Dict]:
    """Retorna as N consultas mais realizadas organizadas por contagem decrescente.
    
    SEC-007: Todas as queries DEVEM usar parameterized statements (?).
    NUNCA interpolar variáveis diretamente em strings SQL.
    """
    # Validação defensiva do parâmetro
    limit = max(1, min(int(limit), 50))
    try:
        init_analytics_db()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT canonical_prompt, count FROM query_stats ORDER BY count DESC, updated_at DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [{"prompt": row["canonical_prompt"], "count": row["count"]} for row in rows]
    except Exception as e:
        logging.error(f"Erro ao buscar sugestões no SQLite: {e}")
        return [
            {"prompt": prompt, "count": count} for prompt, count, _ in INITIAL_SEEDS[:limit]
        ]


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
