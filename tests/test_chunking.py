"""SDD: chunking semântico + enriquecimento de metadata na ingestão Pinecone."""
import sys
import unittest
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from pipelines.ingestion.pinecone_ingestor import (
    _split_sentences,
    _chunk_sentences,
    enrich_metadata,
)


class TestChunking(unittest.TestCase):
    def test_semantic_split_nao_corta_sentenca(self):
        texto = (
            "A reforma tributária unifica impostos sobre consumo. "
            "O Senado debateu a PEC durante três sessões. "
            "Os deputados aprovaram o texto-base por ampla maioria. "
            "A lei complementar regulamenta o novo IVA dual."
        )
        sentences = _split_sentences(texto)
        self.assertEqual(len(sentences), 4)

        chunks = _chunk_sentences(sentences, chunk_size=80, overlap_sentences=1)
        self.assertGreater(len(chunks), 1)

        for sentence in sentences:
            self.assertTrue(any(sentence in chunk for chunk in chunks))

    def test_semantic_split_overlap_entre_chunks(self):
        texto = (
            "Primeira sentença do documento legislativo. "
            "Segunda sentença sobre votação nominal. "
            "Terceira sentença sobre emendas parlamentares. "
            "Quarta sentença sobre sanção presidencial."
        )
        sentences = _split_sentences(texto)
        chunks = _chunk_sentences(sentences, chunk_size=90, overlap_sentences=1)

        self.assertGreaterEqual(len(chunks), 2)
        # Overlap estratégico: a última sentença do chunk N abre o chunk N+1.
        first_tail = chunks[0].rstrip().split(".")[-2].strip() + "."
        self.assertIn(first_tail, chunks[1])

    def test_enrich_metadata_doc_type(self):
        self.assertEqual(enrich_metadata({"source": "votacao_pln_12_2026.txt"})["doc_type"], "votacao")
        self.assertEqual(enrich_metadata({"source": "tse_bens_declaracao_2026.pdf"})["doc_type"], "tse_bens")
        self.assertEqual(enrich_metadata({"source": "senado_materia_42.txt"})["doc_type"], "senado")
        self.assertEqual(enrich_metadata({"source": "transparencia_cgu_gastos.json"})["doc_type"], "transparencia")
        self.assertEqual(enrich_metadata({"source": "lupa_checagem_fatos.html"})["doc_type"], "fact_check")

    def test_enrich_metadata_title_e_date(self):
        enriched = enrich_metadata({"source": "votacao_pln_2026_05_12.txt"})

        self.assertEqual(enriched["title"], "votacao_pln_2026_05_12")
        self.assertEqual(enriched["date"], "2026-05-12")

    def test_enrich_metadata_preserva_source_original(self):
        original = {"source": "votacao_42.txt", "extra": "mantido"}
        enriched = enrich_metadata(original)

        self.assertEqual(enriched["source"], "votacao_42.txt")
        self.assertEqual(enriched["extra"], "mantido")


if __name__ == "__main__":
    unittest.main()
