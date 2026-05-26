import chromadb
from config import settings

client = chromadb.PersistentClient(path=str(settings.chroma_dir))
collection = client.get_or_create_collection(settings.chroma_collection)

def add_documents(chunks: list[str], embeddings: list[list[float]], metadatas: list[dict]):
    ids = [f"{m['filename']}_{m['chunk_index']}" for m in metadatas]
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

def query(embedding: list[float], top_k: int) -> list[dict]:
    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas"]
    )
    return [
        {"texto": doc, "metadata": meta}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]

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