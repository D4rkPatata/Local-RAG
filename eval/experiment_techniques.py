"""
experiment_techniques.py — Exploración de señales de recuperación para el paper.

No toca el código de producción: reutiliza los rankings internos del retriever
(embeddings, LDA) y añade BM25 (señal léxica/dispersa) y TF-IDF como candidatas,
para ver qué combinación por RRF supera a embeddings solo.

Objetivo: comprobar la hipótesis de que en QA corporativo factual el complemento
útil de los embeddings es una señal LÉXICA (BM25), no la temática (LDA).

Uso:
    python eval/experiment_techniques.py
"""
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "localrag"))

from rank_bm25 import BM25Okapi  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

from rag.embedder import embed  # noqa: E402
from rag.vectorstore import _semantic_ranking, _lda_ranking, _rrf, get_all_chunks  # noqa: E402
from config import settings  # noqa: E402

QA_PATH = ROOT / "corpus" / "ground_truth" / "nexus_qa_pairs.json"

# --- Corpus en memoria (mismos chunks que ChromaDB) ------------------------
_data = get_all_chunks()
_ids, _docs, _metas = _data["ids"], _data["documents"], _data["metadatas"]
_tokenized = [d.lower().split() for d in _docs]
_bm25 = BM25Okapi(_tokenized)
_tfidf = TfidfVectorizer()
_tfidf_matrix = _tfidf.fit_transform(_docs)


def _item(i: int) -> dict:
    return {"id": _ids[i], "texto": _docs[i], "metadata": _metas[i]}


def bm25_ranking(query: str, n: int) -> list[dict]:
    scores = _bm25.get_scores(query.lower().split())
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [_item(i) for i in order[:n] if scores[i] > 0]


def tfidf_ranking(query: str, n: int) -> list[dict]:
    qv = _tfidf.transform([query])
    sims = cosine_similarity(qv, _tfidf_matrix)[0]
    order = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)
    return [_item(i) for i in order[:n] if sims[i] > 0]


def emb_ranking(query: str, n: int) -> list[dict]:
    return _semantic_ranking(embed(query), n)


def lda_ranking(query: str, n: int) -> list[dict]:
    return _lda_ranking(query, n)


def _doc_of(chunk: dict) -> str:
    return chunk["metadata"]["filename"].split("_")[0]


def evaluar(rank_fn, qa, top_k, pool) -> dict:
    p1 = p3 = mrr = 0.0
    for par in qa:
        gold = par["doc_id"]
        docs = [_doc_of(c) for c in rank_fn(par["question"], top_k, pool)]
        p1 += 1.0 if docs[:1] == [gold] else 0.0
        p3 += sum(1 for d in docs[:3] if d == gold) / 3.0
        mrr += next((1.0 / (i + 1) for i, d in enumerate(docs) if d == gold), 0.0)
    n = len(qa)
    return {"P@1": p1 / n, "P@3": p3 / n, "MRR": mrr / n}


def main() -> None:
    qa = json.loads(QA_PATH.read_text(encoding="utf-8"))["qa_pairs"]
    top_k = settings.top_k
    pool = top_k * 2

    # Cada técnica como función (query, top_k, pool) -> lista de chunks
    solo = lambda fn: (lambda q, k, p: fn(q, p)[:k])
    fus = lambda *fns: (lambda q, k, p: _rrf(*[fn(q, p) for fn in fns], top_k=k))

    tecnicas = {
        "solo_embeddings": solo(emb_ranking),
        "solo_bm25": solo(bm25_ranking),
        "solo_tfidf": solo(tfidf_ranking),
        "solo_lda": solo(lda_ranking),
        "emb + bm25": fus(emb_ranking, bm25_ranking),
        "emb + lda": fus(emb_ranking, lda_ranking),
        "emb + bm25 + lda": fus(emb_ranking, bm25_ranking, lda_ranking),
    }

    print("=" * 58)
    print(f"  Exploración de técnicas ({len(qa)} Q&A, top_k={top_k})")
    print("=" * 58)
    print(f"\n{'Técnica':<22}{'P@1':>8}{'P@3':>8}{'MRR':>8}")
    print("-" * 46)
    resultados = {}
    for nombre, fn in tecnicas.items():
        m = evaluar(fn, qa, top_k, pool)
        resultados[nombre] = m
        print(f"{nombre:<22}{m['P@1']:>8.3f}{m['P@3']:>8.3f}{m['MRR']:>8.3f}")

    emb = resultados["solo_embeddings"]["MRR"]
    best = max(resultados, key=lambda t: resultados[t]["MRR"])
    print(f"\nMejor técnica por MRR: {best} ({resultados[best]['MRR']:.3f})")
    print(f"Baseline solo_embeddings MRR: {emb:.3f}")


if __name__ == "__main__":
    main()
