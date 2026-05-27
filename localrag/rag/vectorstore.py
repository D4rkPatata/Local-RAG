import chromadb
from rank_bm25 import BM25Okapi
from config import settings

client = chromadb.PersistentClient(path=str(settings.chroma_dir))
collection = client.get_or_create_collection(settings.chroma_collection)

# BM25 se construye en memoria cada vez que se necesita
def _build_bm25():
    results = collection.get(include=["documents"])
    docs = results["documents"]
    if not docs:
        return None, []
    tokenized = [doc.lower().split() for doc in docs]
    return BM25Okapi(tokenized), docs

def add_documents(chunks: list[str], embeddings: list[list[float]], metadatas: list[dict]):
    ids = [f"{m['filename']}_{m['chunk_index']}" for m in metadatas]
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

def query(embedding: list[float], pregunta: str, top_k: int) -> list[dict]:
    # 1. Búsqueda semántica
    semantic = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k * 2, collection.count() or 1),
        include=["documents", "metadatas"]
    )
    semantic_chunks = [
        {"texto": doc, "metadata": meta}
        for doc, meta in zip(semantic["documents"][0], semantic["metadatas"][0])
    ]

    # 2. Búsqueda BM25
    bm25, all_docs = _build_bm25()
    bm25_chunks = []
    if bm25:
        scores = bm25.get_scores(pregunta.lower().split())
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k * 2]
        all_results = collection.get(include=["documents", "metadatas"])
        bm25_chunks = [
            {"texto": all_results["documents"][i], "metadata": all_results["metadatas"][i]}
            for i in top_indices if scores[i] > 0
        ]

    # 3. Reciprocal Rank Fusion (RRF)
    return _rrf(semantic_chunks, bm25_chunks, top_k)

def _rrf(lista_a: list[dict], lista_b: list[dict], top_k: int, k: int = 60) -> list[dict]:
    scores = {}
    for rank, item in enumerate(lista_a):
        key = item["texto"][:100]
        scores[key] = scores.get(key, {"score": 0, "item": item})
        scores[key]["score"] += 1 / (k + rank + 1)

    for rank, item in enumerate(lista_b):
        key = item["texto"][:100]
        if key not in scores:
            scores[key] = {"score": 0, "item": item}
        scores[key]["score"] += 1 / (k + rank + 1)

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    return [r["item"] for r in ranked[:top_k]]

def list_documents() -> list[str]:
    results = collection.get(include=["metadatas"])
    nombres = {m["filename"] for m in results["metadatas"]}
    return list(nombres)

def delete_document(filename: str):
    results = collection.get(include=["metadatas"])
    ids = [
        results["ids"][i]
        for i, m in enumerate(results["metadatas"])
        if m["filename"] == filename
    ]
    if ids:
        collection.delete(ids=ids)