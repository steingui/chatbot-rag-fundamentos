"""RAG-110: Benchmark eval_merge.py — taxa de alucinação em perguntas complexas."""
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import scripts.eval_merge as ev


def test_dataset_contem_perguntas_complexas_com_gabarito():
    cases = ev.load_dataset()

    assert len(cases) >= 5
    for case in cases:
        assert case["query"].strip()
        assert case["ground_truth"].strip()
        # Perguntas complexas (não-factuais simples): exigem síntese/multi-hop
        assert len(case["query"]) > 20


def test_f1_score_comparacao_de_tokens():
    assert ev.f1_tokens("", "") == 0.0
    assert ev.f1_tokens("abc", "abc") == 1.0
    assert ev.f1_tokens("abc", "xyz") == 0.0

    score = ev.f1_tokens("o senador votou sim", "o senador votou sim na sessão")
    assert 0.0 < score <= 1.0


def test_eval_merge_calcula_taxa_alucinacao_e_merge_score():
    answers = [
        {"query": "Como votou Alan Rick na PLP 192?",
         "ground_truth": "Alan Rick votou Sim",
         "answer": "Alan Rick votou Sim",
         "sources": [{"label": "Histórico de Votação"}]},
        {"query": "Como votou Alan Rick na PLP 192?",
         "ground_truth": "Alan Rick votou Sim",
         "answer": "Não sei dizer",
         "sources": []},
    ]

    report = ev.evaluate(answers)

    assert "hallucination_rate" in report
    assert "merge_score" in report
    assert report["hallucination_rate"] == 0.0
    assert report["merge_score"] == 1.0
    assert report["total"] == 2


def test_main_sem_api_usa_mock_e_gera_relatorio():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("PINECONE_API_KEY", None)
        os.environ.pop("OPENROUTER_API_KEY", None)
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GOOGLE_API_KEY", None)

        with patch.object(ev, "run_rag_query", return_value=("MOCK ANSWER", [{"label": "Histórico de Votação"}])) as mocked:
            report = ev.main(["--mock"])

        assert mocked.called
        assert report["total"] >= 5
        assert "hallucination_rate" in report
        assert "merge_score" in report
