"""
lda_model.py — Modelo LDA (Latent Dirichlet Allocation) a nivel de chunk.

Entrena un LDA con gensim sobre los MISMOS chunks indexados en ChromaDB y
expone `lda_scores(query) -> {chunk_id: score}`, donde el score es la
similitud coseno entre la distribución de tópicos de la consulta y la de cada
chunk. Trabajar a nivel de chunk (no de documento) deja a LDA en el mismo
espacio que embeddings y BM25, para que los tres rankings sean comparables y
fusionables (modos solo_embeddings / solo_lda / hibrido del retriever).

Uso:
    python -m rag.lda_model        # entrena y persiste el modelo
    from rag.lda_model import lda_scores
"""
import re

import numpy as np
from gensim import corpora
from gensim.models import LdaModel

from config import settings
from rag.vectorstore import get_all_chunks

NUM_TOPICS = 10
RANDOM_STATE = 42
PASSES = 10

MODEL_DIR = settings.chroma_dir.parent / "lda_model"
DICT_PATH = MODEL_DIR / "dictionary.dict"
LDA_PATH = MODEL_DIR / "lda.model"
MATRIX_PATH = MODEL_DIR / "chunk_topics.npz"

# Stopwords en español (lista compacta para no añadir dependencia de nltk).
STOPWORDS_ES = {
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con",
    "contra", "cual", "cuando", "de", "del", "desde", "donde", "durante", "e",
    "el", "ella", "ellas", "ellos", "en", "entre", "era", "erais", "eran",
    "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos", "esta", "estaba",
    "estada", "estado", "estamos", "estan", "estar", "estas", "este", "esto",
    "estos", "estoy", "fin", "fue", "fueron", "fui", "ha", "habia", "han",
    "hasta", "hay", "la", "las", "le", "les", "lo", "los", "mas", "me", "mi",
    "mis", "mucho", "muchos", "muy", "nada", "ni", "no", "nos", "nosotros",
    "nuestra", "nuestro", "o", "os", "otra", "otras", "otro", "otros", "para",
    "pero", "poco", "por", "porque", "que", "quien", "quienes", "se", "sea",
    "segun", "ser", "si", "sin", "sobre", "solo", "son", "su", "sus", "tambien",
    "tanto", "te", "tiene", "tienen", "toda", "todas", "todo", "todos", "tu",
    "tus", "un", "una", "uno", "unos", "vosotros", "y", "ya", "yo",
    # apoyo de dominio corporativo (palabras de relleno muy frecuentes)
    "debe", "deben", "podra", "podran", "cada", "asi", "ademas", "dentro",
    "caso", "casos", "mismo", "misma", "través", "traves",
}

_TOKEN_RE = re.compile(r"[a-záéíóúñü]+", re.IGNORECASE)


def _tokenize(texto: str) -> list[str]:
    tokens = _TOKEN_RE.findall(texto.lower())
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS_ES]


# --- estado cargado de forma perezosa -------------------------------------
_dictionary: corpora.Dictionary | None = None
_lda: LdaModel | None = None
_chunk_ids: list[str] | None = None
_chunk_topics: np.ndarray | None = None  # (n_chunks, NUM_TOPICS)


def _topic_vector(bow) -> np.ndarray:
    """Distribución densa de tópicos (longitud NUM_TOPICS) para un BoW."""
    dense = np.zeros(NUM_TOPICS, dtype=np.float32)
    for topic_id, prob in _lda.get_document_topics(bow, minimum_probability=0.0):
        dense[topic_id] = prob
    return dense


def train() -> int:
    """Entrena el LDA sobre los chunks de ChromaDB y persiste el modelo.

    Devuelve la cantidad de chunks usados.
    """
    global _dictionary, _lda, _chunk_ids, _chunk_topics

    data = get_all_chunks()
    ids = data["ids"]
    docs = data["documents"]
    if not docs:
        raise RuntimeError(
            "No hay chunks en ChromaDB. Corre scripts/reindex_nexus.py primero."
        )

    tokenized = [_tokenize(d) for d in docs]
    dictionary = corpora.Dictionary(tokenized)
    # Quita términos demasiado raros o demasiado comunes (ruido para LDA).
    dictionary.filter_extremes(no_below=2, no_above=0.5)
    corpus = [dictionary.doc2bow(t) for t in tokenized]

    lda = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=NUM_TOPICS,
        random_state=RANDOM_STATE,
        passes=PASSES,
        alpha="auto",
        eta="auto",
    )

    _dictionary, _lda = dictionary, lda
    topics = (
        np.vstack([_topic_vector(b) for b in corpus])
        if corpus
        else np.zeros((0, NUM_TOPICS), dtype=np.float32)
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    dictionary.save(str(DICT_PATH))
    lda.save(str(LDA_PATH))
    np.savez(MATRIX_PATH, ids=np.array(ids, dtype=object), topics=topics)

    _chunk_ids, _chunk_topics = ids, topics
    return len(ids)


def _ensure_loaded() -> None:
    global _dictionary, _lda, _chunk_ids, _chunk_topics
    if _lda is not None:
        return
    if not LDA_PATH.exists():
        raise RuntimeError(
            "Modelo LDA no entrenado. Corre: python -m rag.lda_model"
        )
    _dictionary = corpora.Dictionary.load(str(DICT_PATH))
    _lda = LdaModel.load(str(LDA_PATH))
    npz = np.load(MATRIX_PATH, allow_pickle=True)
    _chunk_ids = npz["ids"].tolist()
    _chunk_topics = npz["topics"]


def lda_scores(texto: str) -> dict[str, float]:
    """Similitud coseno de tópicos entre `texto` y cada chunk indexado."""
    _ensure_loaded()
    if not _chunk_ids:
        return {}
    q = _topic_vector(_dictionary.doc2bow(_tokenize(texto)))
    qn = np.linalg.norm(q)
    if qn == 0:
        return {cid: 0.0 for cid in _chunk_ids}
    norms = np.linalg.norm(_chunk_topics, axis=1)
    norms[norms == 0] = 1e-9
    sims = (_chunk_topics @ q) / (norms * qn)
    return {cid: float(s) for cid, s in zip(_chunk_ids, sims)}


if __name__ == "__main__":
    n = train()
    print(f"✓ LDA entrenado sobre {n} chunks (num_topics={NUM_TOPICS}).")
    print(f"  Modelo guardado en: {MODEL_DIR}")
