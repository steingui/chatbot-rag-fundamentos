import logging
from typing import List, Dict, Any
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

class HybridRetriever:
    """Retriever Híbrido integrando busca vetorial densa (Pinecone) e lexical esparsa (BM25) com RRF."""

    def __init__(self, dense_retriever: Any, documents: List[Document] = None, k_dense: int = 4, k_bm25: int = 4, rrf_k: int = 60):
        self.dense_retriever = dense_retriever
        self.k_dense = k_dense
        self.k_bm25 = k_bm25
        self.rrf_k = rrf_k
        self.bm25_model = None
        self.documents = documents or []
        
        if self.documents:
            self._build_bm25_index(self.documents)

    def _build_bm25_index(self, documents: List[Document]):
        self.documents = documents
        corpus = [doc.page_content.lower().split() for doc in documents]
        if corpus:
            self.bm25_model = BM25Okapi(corpus)

    def _get_bm25_top_k(self, query: str, top_k: int = 4) -> List[Document]:
        if not self.bm25_model or not self.documents:
            return []
        tokenized_query = query.lower().split()
        scores = self.bm25_model.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [self.documents[i] for i in top_indices if scores[i] > 0]

    def reciprocal_rank_fusion(self, results_list: List[List[Document]], top_n: int = 4) -> List[Document]:
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        for docs in results_list:
            for rank, doc in enumerate(docs):
                doc_key = doc.page_content.strip()
                doc_map[doc_key] = doc
                score = 1.0 / (self.rrf_k + rank + 1)
                doc_scores[doc_key] = doc_scores.get(doc_key, 0.0) + score

        sorted_keys = sorted(doc_scores.keys(), key=lambda k: doc_scores[k], reverse=True)[:top_n]
        return [doc_map[k] for k in sorted_keys]

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> List[Document]:
        query = input if isinstance(input, str) else str(input)
        return self.get_relevant_documents(query)

    def get_relevant_documents(self, query: str) -> List[Document]:
        dense_docs = []
        try:
            if hasattr(self.dense_retriever, "invoke"):
                dense_docs = self.dense_retriever.invoke(query)
            elif hasattr(self.dense_retriever, "get_relevant_documents"):
                dense_docs = self.dense_retriever.get_relevant_documents(query)
        except Exception as e:
            logging.warning(f"Aviso no dense retriever: {e}")

        bm25_docs = self._get_bm25_top_k(query, top_k=self.k_bm25)

        if dense_docs and bm25_docs:
            return self.reciprocal_rank_fusion([dense_docs, bm25_docs], top_n=self.k_dense)
        elif dense_docs:
            return dense_docs[:self.k_dense]
        elif bm25_docs:
            return bm25_docs[:self.k_bm25]
        return []
