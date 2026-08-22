import re
from collections import Counter
import mmh3

class FastBM25Encoder:
    """
    Um encoder de vetores esparsos extremamente leve para o Pinecone.
    Substitui o pinecone_text.sparse.BM25Encoder para evitar:
    1. Downloads gigantes do NLTK (punkt_tab, stopwords).
    2. OOM (Out of Memory) no Render.
    3. Tempo de inicialização (timeout na primeira requisição).
    """
    def __init__(self):
        pass

    def _encode(self, text: str):
        # Tokenização simples (adequada para Português, sem dependência do NLTK)
        words = re.findall(r'\w+', text.lower())
        counts = Counter(words)
        
        indices = []
        values = []
        for w, c in counts.items():
            # mmh3 hash como unsigned int32, idêntico ao pinecone-text
            indices.append(mmh3.hash(w, signed=False))
            # Utiliza a frequência do termo (TF) como peso básico (suficiente para o Hybrid Search com Reranker)
            values.append(float(c))
            
        return {"indices": indices, "values": values}

    def encode_queries(self, text: str):
        return self._encode(text)

    def encode_documents(self, text: str):
        return self._encode(text)
