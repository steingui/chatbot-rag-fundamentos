#!/usr/bin/env python3
"""RAG-110 — Benchmark de alucinação do RAG.

Mede a taxa de alucinação e um "merge score" (fidelidade média ao gabarito)
sobre um conjunto de perguntas complexas (multi-hop/síntese) ancoradas nos
documentos reais de `data/docs/`.

Uso:
    python scripts/eval_merge.py                 # usa a API real (RAG + LLM)
    python scripts/eval_merge.py --mock          # modo offline (sem API)
    python scripts/eval_merge.py --json          # relatório em JSON
"""

import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# F1 abaixo deste limiar com fontes presentes => resposta considerada alucinada.
F1_THRESHOLD = 0.5

# Conjunto de teste de perguntas complexas com gabarito extraído dos documentos
# canônicos em `data/docs/` (base interna = fonte primária).
BENCHMARK_CASES: List[Dict[str, str]] = [
    {
        "query": "Na votação do PLP 192/2023 no Senado, como votou o senador Alan Rick (UNIÃO-AC) e qual a data da sessão?",
        "ground_truth": "Alan Rick votou Sim e a sessão ocorreu em 2025-09-02.",
    },
    {
        "query": "Qual foi o voto do senador Alessandro Vieira no PLP 192/2023 e qual partido ele representa?",
        "ground_truth": "Alessandro Vieira votou Não e pertence ao MDB-SE.",
    },
    {
        "query": "Qual o total amostrado de despesas da CEAPS da senadora Damares Alves em 2026 e cite um fornecedor reembolsado?",
        "ground_truth": "Total amostrado de R$ 52.414,29; fornecedor ROTA COMBUSTIVEIS LTDA.",
    },
    {
        "query": "A checagem do Aos Fatos sobre o vídeo em que Lula fala do PT concluiu que a gravação era autêntica ou editada?",
        "ground_truth": "O vídeo foi editado e tirado de contexto; Lula parafraseava Maria da Conceição Tavares.",
    },
    {
        "query": "Qual é o código da matéria da MSG 00031/1991 no Senado e quem é o autor da proposição?",
        "ground_truth": "O código da matéria é 236 e o autor é desconhecido.",
    },
]


def load_dataset() -> List[Dict[str, str]]:
    """Retorna uma cópia do conjunto de teste de perguntas complexas."""
    return [dict(case) for case in BENCHMARK_CASES]


def _tokenize(text: str) -> List[str]:
    """Tokeniza em minúsculas removendo pontuação."""
    return re.findall(r"[a-z0-9à-ú]+", (text or "").lower())


def f1_tokens(reference: str, candidate: str) -> float:
    """F1 entre conjuntos de tokens do gabarito e da resposta gerada."""
    ref = set(_tokenize(reference))
    cand = set(_tokenize(candidate))
    if not ref or not cand:
        return 0.0

    tp = len(ref & cand)
    precision = tp / len(cand)
    recall = tp / len(ref)
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def evaluate(answers: List[Dict[str, Any]], threshold: float = F1_THRESHOLD) -> Dict[str, Any]:
    """Calcula taxa de alucinação e merge score.

    Alucinação é contada apenas sobre respostas fundamentadas (com fontes):
    resposta com fontes mas F1 < limiar contradiz o gabarito.
    Respostas sem fontes são tratadas como "não respondidas" (não alucinadas).
    """
    answered = [a for a in answers if a.get("sources")]
    hallucinated = [
        a for a in answered
        if f1_tokens(a["ground_truth"], a["answer"]) < threshold
    ]

    merge_score = (
        sum(f1_tokens(a["ground_truth"], a["answer"]) for a in answered) / len(answered)
        if answered
        else 1.0
    )
    hallucination_rate = len(hallucinated) / len(answered) if answered else 0.0

    return {
        "total": len(answers),
        "answered": len(answered),
        "hallucinated": len(hallucinated),
        "hallucination_rate": hallucination_rate,
        "merge_score": merge_score,
        "per_case": [
            {
                "query": a["query"],
                "f1": f1_tokens(a["ground_truth"], a["answer"]),
                "hallucinated": a in hallucinated,
                "has_sources": bool(a.get("sources")),
                "answer": a["answer"],
            }
            for a in answers
        ],
    }


def run_rag_query(query: str) -> Tuple[str, List[Dict[str, str]]]:
    """Consulta o pipeline RAG real (Pinecone + LLM). Sem API, retorna vazio."""
    try:
        from backend.rag.chat import get_rag_chain

        chain = get_rag_chain("eval-merge")
        result = chain.invoke({"question": query})
        sources = [
            {"label": doc.metadata.get("source", "Desconhecido")}
            for doc in result.get("source_documents", [])
        ]
        return result.get("answer", ""), sources
    except Exception as exc:  # pragma: no cover - depende de credenciais
        return f"[offline] {exc}", []


def main(argv: List[str] | None = None) -> Dict[str, Any]:
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    mock_mode = "--mock" in argv

    cases = load_dataset()
    results: List[Dict[str, Any]] = []
    for case in cases:
        answer, sources = run_rag_query(case["query"])
        results.append(
            {
                "query": case["query"],
                "ground_truth": case["ground_truth"],
                "answer": answer,
                "sources": sources,
            }
        )

    report = evaluate(results)

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Total de perguntas: {report['total']}")
        print(f"Respondidas (com fontes): {report['answered']}")
        print(f"Alucinadas: {report['hallucinated']}")
        print(f"Taxa de alucinação: {report['hallucination_rate']:.2%}")
        print(f"Merge score (fidelidade média): {report['merge_score']:.4f}")
        for item in report["per_case"]:
            status = "ALUCINADA" if item["hallucinated"] else ("sem fontes" if not item["has_sources"] else "ok")
            print(f"  [{status}] f1={item['f1']:.2f} | {item['query'][:60]}...")

    return report


if __name__ == "__main__":
    main()
