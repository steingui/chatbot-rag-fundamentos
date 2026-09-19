import heapq
import logging
import re
import unicodedata
from typing import Any, Dict, List

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi


class HybridRetriever:
    """Retriever Híbrido otimizado integrando busca vetorial densa (Pinecone) e lexical esparsa (BM25) com RRF."""

    def __init__(self, dense_retriever: Any, documents: List[Document] = None, k_dense: int = 4, k_bm25: int = 4, rrf_k: int = 60):
        self.dense_retriever = dense_retriever
        self.k_dense = k_dense
        self.k_bm25 = k_bm25
        self.rrf_k = rrf_k
        self.bm25_model = None
        self.documents = documents or []

        if self.documents:
            self._build_bm25_index(self.documents)

    def _tokenize(self, text: str) -> List[str]:
        ascii_text = unicodedata.normalize('NFKD', text.lower()).encode('ascii', 'ignore').decode('ascii')
        return re.findall(r'\w+', ascii_text)

    def _build_bm25_index(self, documents: List[Document]) -> None:
        self.documents = documents
        corpus = [self._tokenize(doc.page_content) for doc in documents]
        if corpus:
            self.bm25_model = BM25Okapi(corpus)

    def _get_bm25_top_k(self, query: str, top_k: int = 4) -> List[Document]:
        if not self.bm25_model or not self.documents:
            return []
        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return []
        scores = self.bm25_model.get_scores(tokenized_query)
        top_indices = heapq.nlargest(top_k, range(len(scores)), key=scores.__getitem__)
        return [self.documents[i] for i in top_indices if scores[i] > 0]

    def reciprocal_rank_fusion(self, results_list: List[List[Document]], top_n: int = 4) -> List[Document]:
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        for list_idx, docs in enumerate(results_list):
            # Atribui peso ligeiramente maior (1.2) para resultados densos se disponíveis
            weight = 1.2 if list_idx == 0 else 1.0
            for rank, doc in enumerate(docs):
                doc_key = doc.page_content.strip()
                doc_map[doc_key] = doc
                doc_scores[doc_key] = doc_scores.get(doc_key, 0.0) + weight / (self.rrf_k + rank + 1)

        top_keys = heapq.nlargest(top_n, doc_scores, key=doc_scores.__getitem__)
        return [doc_map[k] for k in top_keys]

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> List[Document]:
        return self.get_relevant_documents(input if isinstance(input, str) else str(input))

    def get_relevant_documents(self, query: str) -> List[Document]:
        dense_docs = self._get_dense_docs(query)
        bm25_docs = self._get_bm25_top_k(query, top_k=self.k_bm25)

        if dense_docs and bm25_docs:
            return self.reciprocal_rank_fusion([dense_docs, bm25_docs], top_n=self.k_dense)
        if dense_docs:
            return dense_docs[:self.k_dense]
        if bm25_docs:
            return bm25_docs[:self.k_bm25]
        return []

    def _get_dense_docs(self, query: str) -> List[Document]:
        try:
            get = getattr(self.dense_retriever, "invoke", None) or getattr(self.dense_retriever, "get_relevant_documents", None)
            if get:
                return get(query)
        except Exception as e:
            logging.warning(f"Aviso no dense retriever: {e}")
        return []
