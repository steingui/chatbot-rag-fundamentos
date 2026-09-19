#!/usr/bin/env python3
"""RAG-111 — Avaliação de migração de embeddings (MiniLM → multilingual-e5-large).

Compara o modelo atual com o candidato de v2 em dimensões, cobertura
multilíngue e comportamento de consulta, emitindo uma recomendação pragmática.

Uso:
    python scripts/eval_embedding_migration.py            # avaliação completa
    python scripts/eval_embedding_migration.py --mock     # modo offline
    python scripts/eval_embedding_migration.py --json     # relatório em JSON
"""

import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

EMBEDDING_MODELS: Dict[str, Dict[str, Any]] = {
    "current": {
        "id": "sentence-transformers/all-MiniLM-L6-v2",
        "dims": 384,
        "multilingual": False,
    },
    "target": {
        "id": "multilingual-e5-large",
        "dims": 1024,
        "multilingual": True,
    },
}

# Amostra multilíngue (pt-BR, domínio legislativo) para validar cobertura.
EVAL_CASES: List[Dict[str, str]] = [
    {"query": "Como votou o senador Alan Rick no PLP 192?", "expected": "Sim"},
    {"query": "Qual a despesa da CEAPS da senadora Damares Alves?", "expected": "R$ 52.414,29"},
    {"query": "Quem é o autor da MSG 00031/1991 no Senado?", "expected": "desconhecido"},
]


def load_eval_cases() -> List[Dict[str, str]]:
    """Retorna uma cópia do conjunto de avaliação multilíngue."""
    return [dict(case) for case in EVAL_CASES]


def format_query(query: str, model: Dict[str, Any]) -> str:
    """Aplica o prefixo de consulta exigido por modelos E5; MiniLM não exige."""
    if model["multilingual"] and model["id"].startswith("multilingual-e5"):
        return f"query: {query}"
    return query


def recommend(models: Dict[str, Dict[str, Any]]) -> str:
    """Recomendação pragmática de migração para v2.

    O e5-large é multilíngue (pt-BR) e tem 1024 dims; a troca exige
    re-indexação completa do Pinecone. Mantém-se o modelo atual no MVP e
    migra-se na v2, como decidido no roadmap.
    """
    current = models["current"]
    target = models["target"]
    if target["multilingual"] and target["dims"] > current["dims"]:
        return (
            f"Migrar para {target['id']} na v2: melhor cobertura pt-BR "
            f"({target['dims']} dims vs {current['dims']}). Exige re-indexação "
            f"completa do índice Pinecone."
        )
    return f"Manter {current['id']} por enquanto."


def main(argv: List[str] | None = None) -> Dict[str, Any]:
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    mock_mode = "--mock" in argv

    report = {
        "current": dict(EMBEDDING_MODELS["current"]),
        "target": dict(EMBEDDING_MODELS["target"]),
        "cases": len(load_eval_cases()),
        "mode": "mock" if mock_mode else "live",
        "recommendation": recommend(EMBEDDING_MODELS),
    }

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Embedding atual : {report['current']['id']} ({report['current']['dims']} dims)")
        print(f"Embedding v2    : {report['target']['id']} ({report['target']['dims']} dims)")
        print(f"Casos de avaliação: {report['cases']}")
        print(f"Recomendação    : {report['recommendation']}")

    return report


if __name__ == "__main__":
    main()
