import airgap  # noqa: F401  — fuerza modo offline / telemetría off antes de chromadb
import chromadb
from chromadb.config import Settings as ChromaSettings
from rank_bm25 import BM25Okapi
from config import settings
from rag.embedder import embed

# anonymized_telemetry=False corta la telemetría de ChromaDB de forma explícita,
# sin depender solo de la variable de entorno.
client = chromadb.PersistentClient(
    path=str(settings.chroma_dir),
    settings=ChromaSettings(anonymized_telemetry=False),
)

# Resolvemos la colección por nombre en cada operación. En chromadb 1.x un
# handle cacheado queda fijado al UUID y se invalida si la colección se borra
# (p. ej. al reindexar), por eso no se guarda a nivel de módulo.
def _get_collection():
    return client.get_or_create_collection(settings.chroma_collection)

def get_all_chunks() -> dict:
    """Todos los chunks indexados: {'ids', 'documents', 'metadatas'}.

    Fuente única de los chunks para el modelo LDA y el benchmark, de modo que
    los tres modos del retriever puntúen exactamente sobre el mismo conjunto.
    """
    collection = _get_collection()
    return collection.get(include=["documents", "metadatas"])

def add_documents(chunks: list[str], embeddings: list[list[float]], metadatas: list[dict]):
    collection = _get_collection()
    ids = [f"{m['filename']}_{m['chunk_index']}" for m in metadatas]
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

MODES = ("hibrido", "solo_embeddings", "solo_bm25", "solo_lda")


def _doc_id_of(meta: dict) -> str:
    """doc_id de un chunk; cae al prefijo Dxx del filename si falta en metadata."""
    return meta.get("doc_id") or meta["filename"].split("_")[0]


def _semantic_ranking(embedding: list[float], n: int, where: dict | None = None) -> list[dict]:
    """Ranking por similitud semántica (ChromaDB). Items: {id, texto, metadata}.

    `where` aplica el filtro de control de acceso en el propio motor (ChromaDB
    solo evalúa los chunks autorizados).
    """
    collection = _get_collection()
    res = collection.query(
        query_embeddings=[embedding],
        n_results=min(n, collection.count() or 1),
        include=["documents", "metadatas"],
        where=where,
    )
    if not res["ids"] or not res["ids"][0]:
        return []
    return [
        {"id": cid, "texto": doc, "metadata": meta}
        for cid, doc, meta in zip(res["ids"][0], res["documents"][0], res["metadatas"][0])
    ]


def _lda_ranking(pregunta: str, n: int, allowed: set[str] | None = None) -> list[dict]:
    """Ranking por similitud de tópicos LDA. Items: {id, texto, metadata}.

    Si `allowed` está presente, se descartan los chunks fuera de clearance ANTES
    de ordenar (el filtro de acceso no se aplica después del ranking).
    """
    # Import diferido: lda_model importa este módulo (get_all_chunks), así que
    # un import a nivel de módulo crearía un ciclo.
    from rag.lda_model import lda_scores

    scores = lda_scores(pregunta)
    if not scores:
        return []
    data = get_all_chunks()
    id2idx = {cid: i for i, cid in enumerate(data["ids"])}
    candidatos = sorted(scores, key=lambda c: scores[c], reverse=True)
    if allowed is not None:
        candidatos = [c for c in candidatos if _doc_id_of(data["metadatas"][id2idx[c]]) in allowed]
    return [
        {
            "id": cid,
            "texto": data["documents"][id2idx[cid]],
            "metadata": data["metadatas"][id2idx[cid]],
        }
        for cid in candidatos[:n]
    ]


def _bm25_ranking(pregunta: str, n: int, allowed: set[str] | None = None) -> list[dict]:
    """Ranking léxico/disperso BM25. Items: {id, texto, metadata}.

    Se reconstruye sobre los chunks indexados en cada consulta (corpus pequeño),
    así refleja altas/bajas de documentos sin estado persistente. Si `allowed`
    está presente, el corpus se filtra por clearance ANTES de construir el índice
    (el IDF se calcula solo sobre los chunks autorizados).
    """
    data = get_all_chunks()
    ids, docs, metas = data["ids"], data["documents"], data["metadatas"]
    if allowed is not None:
        triples = [(i, d, m) for i, d, m in zip(ids, docs, metas) if _doc_id_of(m) in allowed]
        if not triples:
            return []
        ids, docs, metas = map(list, zip(*triples))
    if not docs:
        return []
    bm25 = BM25Okapi([d.lower().split() for d in docs])
    scores = bm25.get_scores(pregunta.lower().split())
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [
        {"id": ids[i], "texto": docs[i], "metadata": metas[i]}
        for i in order[:n] if scores[i] > 0
    ]


def retrieve(pregunta: str, mode: str = "hibrido", top_k: int | None = None,
             embedding: list[float] | None = None, user=None) -> list[dict]:
    """Recupera chunks para `pregunta` según el modo del ablation study.

    - "solo_embeddings": ranking semántico denso (ChromaDB).
    - "solo_bm25":       ranking léxico disperso (BM25).
    - "solo_lda":        ranking de tópicos (LDA) — ablation; señal débil.
    - "hibrido":         RRF de embeddings + BM25 (denso+disperso). Es el modo de
                         producción y la mejor configuración del benchmark.

    Si se pasa `user` (access.User), se aplica control de acceso por tier: solo se
    consideran chunks de documentos para los que el usuario tiene clearance. Sin
    `user`, el comportamiento es idéntico al original (backward compatible).
    """
    if mode not in MODES:
        raise ValueError(f"mode inválido: {mode!r}. Usa uno de {MODES}.")
    top_k = top_k or settings.top_k
    pool = top_k * 2  # se recupera el doble por señal antes de fusionar/cortar

    where = None
    allowed = None
    if user is not None:
        from access import allowed_doc_ids
        allowed = allowed_doc_ids(user)
        if not allowed:
            return []
        where = {"doc_id": {"$in": sorted(allowed)}}

    if mode == "solo_lda":
        return _lda_ranking(pregunta, pool, allowed=allowed)[:top_k]
    if mode == "solo_bm25":
        return _bm25_ranking(pregunta, pool, allowed=allowed)[:top_k]

    if embedding is None:
        embedding = embed(pregunta)
    if mode == "solo_embeddings":
        return _semantic_ranking(embedding, pool, where=where)[:top_k]

    # hibrido: fusión denso + disperso (embeddings + BM25)
    return _rrf(
        _semantic_ranking(embedding, pool, where=where),
        _bm25_ranking(pregunta, pool, allowed=allowed),
        top_k=top_k,
    )


def _rrf(*rankings: list[dict], top_k: int, k: int = 60,
         weights: tuple[float, ...] | None = None) -> list[dict]:
    """Reciprocal Rank Fusion ponderado de N rankings. Deduplica por id de chunk.

    score(chunk) = Σ_i  w_i · 1 / (k + rank_i)
    """
    if weights is None:
        weights = (1.0,) * len(rankings)
    fused: dict[str, dict] = {}
    for w, ranking in zip(weights, rankings):
        for rank, item in enumerate(ranking):
            key = item["id"]
            if key not in fused:
                fused[key] = {"score": 0.0, "item": item}
            fused[key]["score"] += w / (k + rank + 1)
    ranked = sorted(fused.values(), key=lambda x: x["score"], reverse=True)
    return [r["item"] for r in ranked[:top_k]]

def list_documents() -> list[str]:
    collection = _get_collection()
    results = collection.get(include=["metadatas"])
    nombres = {m["filename"] for m in results["metadatas"]}
    return list(nombres)

def delete_document(filename: str):
    collection = _get_collection()
    results = collection.get(include=["metadatas"])
    ids = [
        results["ids"][i]
        for i, m in enumerate(results["metadatas"])
        if m["filename"] == filename
    ]
    if ids:
        collection.delete(ids=ids)