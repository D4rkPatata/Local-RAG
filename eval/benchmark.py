"""
benchmark.py — Ablation study del retriever sobre los 75 pares Q&A de Nexus.

Evalúa los modos de producción (solo_embeddings / solo_bm25 / solo_lda /
hibrido = emb+bm25) y, además, la variante emb+bm25+lda para mostrar que añadir
LDA degrada el híbrido. Reporta P@1, P@3 y MRR.

Relevancia a nivel de documento: un chunk recuperado se considera relevante si
su documento de origen (prefijo Dxx del filename) coincide con el `doc_id` del
par Q&A. Es el proxy estándar cuando no existe ground-truth a nivel de chunk
(el `gt_field` del dataset apunta al JSON de ground truth, no a un chunk).

Uso:
    python eval/benchmark.py
"""
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "localrag"))

from rag.embedder import embed  # noqa: E402
from rag.vectorstore import (  # noqa: E402
    retrieve, _semantic_ranking, _bm25_ranking, _lda_ranking, _rrf,
)
from config import settings  # noqa: E402

QA_PATH = ROOT / "corpus" / "ground_truth" / "nexus_qa_pairs.json"
RESULTS_PATH = Path(__file__).parent / "results.json"


def _doc_of(chunk: dict) -> str:
    """Prefijo Dxx del documento de origen de un chunk recuperado."""
    return chunk["metadata"]["filename"].split("_")[0]


def cargar_qa() -> list[dict]:
    return json.loads(QA_PATH.read_text(encoding="utf-8"))["qa_pairs"]


def _construir_modos(top_k: int):
    """Mapa nombre -> función(pregunta) -> chunks. Incluye la ablation +lda."""
    pool = top_k * 2

    def hibrido_lda(q: str) -> list[dict]:
        return _rrf(
            _semantic_ranking(embed(q), pool),
            _bm25_ranking(q, pool),
            _lda_ranking(q, pool),
            top_k=top_k,
        )

    return {
        "solo_embeddings": lambda q: retrieve(q, "solo_embeddings", top_k),
        "solo_bm25": lambda q: retrieve(q, "solo_bm25", top_k),
        "solo_lda": lambda q: retrieve(q, "solo_lda", top_k),
        "hibrido (emb+bm25)": lambda q: retrieve(q, "hibrido", top_k),
        "+lda (emb+bm25+lda)": hibrido_lda,
    }


def evaluar(rank_fn, qa: list[dict]) -> dict:
    p1 = p3 = mrr = 0.0
    for par in qa:
        gold = par["doc_id"]
        docs = [_doc_of(c) for c in rank_fn(par["question"])]
        p1 += 1.0 if docs[:1] == [gold] else 0.0
        p3 += sum(1 for d in docs[:3] if d == gold) / 3.0
        mrr += next((1.0 / (i + 1) for i, d in enumerate(docs) if d == gold), 0.0)
    n = len(qa)
    return {"P@1": p1 / n, "P@3": p3 / n, "MRR": mrr / n}


def main() -> None:
    qa = cargar_qa()
    top_k = settings.top_k
    modos = _construir_modos(top_k)

    print("=" * 60)
    print(f"  PrivaceCheck — Ablation retriever ({len(qa)} pares Q&A, top_k={top_k})")
    print("=" * 60)
    print(f"\n{'Modo':<22}{'P@1':>8}{'P@3':>8}{'MRR':>8}")
    print("-" * 46)

    resultados = {}
    for nombre, fn in modos.items():
        m = evaluar(fn, qa)
        resultados[nombre] = m
        print(f"{nombre:<22}{m['P@1']:>8.3f}{m['P@3']:>8.3f}{m['MRR']:>8.3f}")

    hib = resultados["hibrido (emb+bm25)"]["MRR"]
    emb = resultados["solo_embeddings"]["MRR"]
    bm25 = resultados["solo_bm25"]["MRR"]
    mejor = max(resultados, key=lambda t: resultados[t]["MRR"])
    print(f"\nMejor modo por MRR: {mejor} ({resultados[mejor]['MRR']:.3f})")
    gana = hib >= max(emb, bm25)
    print(f"El híbrido emb+bm25 (MRR={hib:.3f}) "
          f"{'SUPERA o iguala' if gana else 'NO supera'} a sus componentes "
          f"(emb={emb:.3f}, bm25={bm25:.3f}).")

    RESULTS_PATH.write_text(
        json.dumps({"top_k": top_k, "n": len(qa), "resultados": resultados},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n✓ Resultados guardados en: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
