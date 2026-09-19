"""RAG-111: Avaliação de migração de embeddings (MiniLM → multilingual-e5-large)."""
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import scripts.eval_embedding_migration as evm


def test_modelos_candidatos_configurados():
    current = evm.EMBEDDING_MODELS["current"]
    target = evm.EMBEDDING_MODELS["target"]

    assert current["id"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert current["dims"] == 384
    assert not current["multilingual"]

    assert target["id"] == "multilingual-e5-large"
    assert target["dims"] == 1024
    assert target["multilingual"]


def test_dataset_de_avaliacao_multilingue():
    cases = evm.load_eval_cases()

    assert len(cases) >= 3
    for case in cases:
        assert case["query"].strip()
        assert case["expected"].strip()


def test_prefixo_de_consulta_apenas_para_e5():
    # Modelos E5 exigem prefixo "query: " para busca; MiniLM não.
    assert evm.format_query("Votação PLP 192", evm.EMBEDDING_MODELS["current"]) == "Votação PLP 192"
    assert evm.format_query("Votação PLP 192", evm.EMBEDDING_MODELS["target"]).startswith("query: ")


def test_mock_avaliacao_gera_recomendacao():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("PINECONE_API_KEY", None)
        os.environ.pop("HF_TOKEN", None)

        report = evm.main(["--mock"])

    assert report["current"]["id"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert report["target"]["id"] == "multilingual-e5-large"
    assert "recommendation" in report
    # Para pt-BR, o modelo multilíngue deve ser a recomendação de v2.
    assert "multilingual-e5-large" in report["recommendation"]
