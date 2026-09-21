# Jev — Análise de Backfill do Banco Vetorial

> Pergunta: faz sentido rodar um backfill no Pinecone por causa do Jev?

---

## 1. Conclusão (resposta curta)

**Não — a integração Jev não exige backfill.** O Jev é camada de decisão sobre
documentos **já recuperados**; ele não altera embeddings, chunks ou metadados.
Os gates R1–R7 do [`JEV_ROADMAP.md`](JEV_ROADMAP.md) operam sobre o índice
atual sem reindexar.

Backfill só se justifica por **outros motivos** (qualidade de recuperação),
não pelo Jev. A decisão deve ser guiada por auditoria, não por suposição.

---

## 2. O que o backfill resolveria (e o que não resolveria)

| Motivo | Backfill resolve? | Relação com Jev |
|--------|-------------------|-----------------|
| Jev precisa de vetores novos | Não se aplica | Nenhuma |
| Metadados (`doc_type`/`title`/`date`) ausentes em chunks antigos | **Sim** (metadata-only) | **Indireta**: R3/R4 (gates de answerability/relevância) se beneficiam de metadados ricos para filtrar e ranquear |
| Chunks órfãos/duplicados | **Sim** (re-ingest) | Indireta: ruído piora o `jev_check` |
| Embedding não multilíngue (MiniLM) | **Sim** (re-index completo) | Nenhuma — decisão de v2 |
| Recência de conteúdo legislativo | **Sim** (re-ingest de fontes) | Indireta: melhora R5 (conflito interno vs web) |

---

## 3. Estado atual do índice

Pontos conhecidos do código:

- Embedding: [`sentence-transformers/all-MiniLM-L6-v2`](pipelines/ingestion/pinecone_ingestor.py:21),
  **384 dims, não multilíngue** — confirmado em
  [`eval_embedding_migration.py`](scripts/eval_embedding_migration.py:20).
- `data/docs/` contém apenas um subdiretório `docs/docs/` — ou seja, **o
  diretório local de ingestão
  está praticamente vazio**. O índice em produção foi populado por pipelines
  (GitHub Actions) e scrapers, não por esse diretório.
- Metadados enriquecidos por [`enrich_metadata()`](pipelines/ingestion/pinecone_ingestor.py:69)
  (`doc_type`, `title`, `date`) — **só existem se o chunk foi ingerido após
  essa função ter sido introduzida**. Chunks antigos podem não ter `doc_type`.

**O que falta saber (auditoria):** contagem real de vetores, dimensão e
cobertura de metadados. Verificar `total_vectors` e `dimension` no console do
Pinecone e complementar com contagem por `doc_type` via filtro de metadados.

---

## 4. Matriz de decisão

| Cenário (após auditoria) | Ação | Custo | Risco |
|--------------------------|------|-------|-------|
| Vetores > 0, metadados `doc_type` presentes | **Nenhum backfill** | 0 | Nenhum |
| Vetores > 0, sem `doc_type` em fração relevante | **Metadata-only** (`index.update`) | Baixo | Baixo |
| Chunks órfãos/duplicados detectados | **Re-ingest das fontes afetadas** | Médio | Médio |
| Decisão de migrar p/ `multilingual-e5-large` (v2) | **Re-index completo** | Alto | Alto (janela de indisponibilidade) |

---

## 5. Procedimentos

### A. Metadata-only (sem re-embedding)

Atualizar só `metadata` dos vetores existentes preservando embeddings e IDs:

```python
# backfill_metadata.py (a criar em code mode, se necessário)
from pinecone import Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos"))

# 1) buscar IDs + metadados atuais via query/scroll
# 2) re-aplicar enrich_metadata() no campo "source"
# 3) index.update(id=..., set_metadata={...}) por lote
```

**Vantagem:** não re-gasta embeddings HF e não derruba o índice.

### B. Re-ingest de fontes afetadas (chunks órfãos)

Re-rodar o ingestor por fonte. O próprio
[`limpar_vetores_antigos_por_fonte()`](pipelines/ingestion/pinecone_ingestor.py:124)
já apaga vetores antigos por `source` antes do upsert, evitando órfãos:

```bash
python pipelines/ingestion/pinecone_ingestor.py
```

### C. Re-index completo (migração de embedding)

Só na v2 e **fora do escopo do Jev**. Requer recriar o índice com dimensão 1024
(`multilingual-e5-large`) e re-ingerir tudo. Ver recomendação em
[`eval_embedding_migration.py`](scripts/eval_embedding_migration.py:53).

---

## 6. Recomendação final

1. **Auditar o índice no console do Pinecone** (contagem de vetores, dimensão e
   cobertura de `doc_type`) antes de qualquer backfill.
2. **Backfill por causa do Jev: não fazer.**
3. **Se a auditoria revelar falta de `doc_type`** em chunks antigos, executar o
   **metadata-only** (procedimento A) — é o único backfill com ROI claro para
   os gates R3/R4, e não re-gasta embeddings.
4. **Re-index completo só na v2** (migração de embedding), como já decidido em
   [`eval_embedding_migration.py`](scripts/eval_embedding_migration.py:53).
