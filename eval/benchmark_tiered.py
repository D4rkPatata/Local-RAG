"""
benchmark_tiered.py — Ablation del retriever estratificada por tier de sensibilidad.

Extiende el benchmark.py original: además del agregado global, reporta P@1, P@3 y MRR
desagregado por tier de sensibilidad del documento. Es la métrica que sustenta el
argumento central del paper: la ganancia de fine-tuning sobre RAG puro depende del
nivel de confidencialidad y vocabulario propietario del corpus.

Tiers:
    Tier-1 (employee-facing):     D01-D08, D15.
    Tier-2 (operacional interno): D09-D14.
    Tier-3 (estratégico confid.): D16-D23.

Entradas:
    corpus/ground_truth/nexus_qa_pairs.json        (75 pares, D01-D15)
    corpus/ground_truth/nexus_qa_pairs_tier3.json  (40 pares, D16-D23)

Uso:
    python eval/benchmark_tiered.py
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "localrag"))

from rag.embedder import embed  # noqa: E402
from rag.vectorstore import (  # noqa: E402
    retrieve, _semantic_ranking, _bm25_ranking, _lda_ranking, _rrf,
)
from config import settings  # noqa: E402

QA_PATH_BASE = ROOT / "corpus" / "ground_truth" / "nexus_qa_pairs.json"
QA_PATH_TIER3 = ROOT / "corpus" / "ground_truth" / "nexus_qa_pairs_tier3.json"
RESULTS_PATH = Path(__file__).parent / "results_tiered.json"

TIER_MAP = {
    # Tier-1 — employee-facing
    "D01": 1, "D02": 1, "D03": 1, "D04": 1, "D05": 1,
    "D06": 1, "D07": 1, "D08": 1, "D15": 1,
    # Tier-2 — operacional interno
    "D09": 2, "D10": 2, "D11": 2, "D12": 2, "D13": 2, "D14": 2,
    # Tier-3 — estratégico confidencial
    "D16": 3, "D17": 3, "D18": 3, "D19": 3,
    "D20": 3, "D21": 3, "D22": 3, "D23": 3,
}

TIER_LABEL = {
    1: "Tier-1 (employee-facing)",
    2: "Tier-2 (operacional interno)",
    3: "Tier-3 (estratégico confidencial)",
}


def _doc_of(chunk: dict) -> str:
    """Prefijo Dxx del documento de origen de un chunk recuperado."""
    return chunk["metadata"]["filename"].split("_")[0]


def cargar_qa() -> list[dict]:
    """Une los Q&A originales (Tier-1/2) y la extensión Tier-3, tageando con tier."""
    base = json.loads(QA_PATH_BASE.read_text(encoding="utf-8"))["qa_pairs"]
    pairs = list(base)
    if QA_PATH_TIER3.exists():
        ext = json.loads(QA_PATH_TIER3.read_text(encoding="utf-8"))["qa_pairs"]
        pairs.extend(ext)
    for p in pairs:
        p["_tier"] = TIER_MAP.get(p["doc_id"], 0)
    sin_tier = [p["doc_id"] for p in pairs if p["_tier"] == 0]
    if sin_tier:
        print(f"AVISO: pares sin tier asignado para doc_ids: {set(sin_tier)}")
    return pairs


def _construir_modos(top_k: int):
    """Mapa nombre -> función(pregunta) -> chunks. Mismo set que benchmark.py."""
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


def _metricas_vacias() -> dict:
    return {"P@1": 0.0, "P@3": 0.0, "MRR": 0.0, "n": 0}


def evaluar_estratificado(rank_fn, qa: list[dict]) -> dict:
    """Calcula métricas global y por tier de un único modo de retrieval."""
    agg = {"global": _metricas_vacias()}
    for t in TIER_LABEL:
        agg[f"tier_{t}"] = _metricas_vacias()

    for par in qa:
        gold = par["doc_id"]
        tier_key = f"tier_{par['_tier']}"
        docs = [_doc_of(c) for c in rank_fn(par["question"])]

        p1 = 1.0 if docs[:1] == [gold] else 0.0
        p3 = sum(1 for d in docs[:3] if d == gold) / 3.0
        mrr = next((1.0 / (i + 1) for i, d in enumerate(docs) if d == gold), 0.0)

        for bucket in ("global", tier_key):
            agg[bucket]["P@1"] += p1
            agg[bucket]["P@3"] += p3
            agg[bucket]["MRR"] += mrr
            agg[bucket]["n"] += 1

    # promedio
    for bucket, vals in agg.items():
        n = vals["n"] or 1
        for k in ("P@1", "P@3", "MRR"):
            vals[k] = vals[k] / n
    return agg


def _print_tabla(titulo: str, resultados: dict, bucket: str, n: int) -> None:
    print(f"\n{titulo}  (n={n})")
    print(f"{'Modo':<24}{'P@1':>8}{'P@3':>8}{'MRR':>8}")
    print("-" * 48)
    for modo, m_por_bucket in resultados.items():
        m = m_por_bucket[bucket]
        print(f"{modo:<24}{m['P@1']:>8.3f}{m['P@3']:>8.3f}{m['MRR']:>8.3f}")


def main() -> None:
    qa = cargar_qa()
    top_k = settings.top_k
    modos = _construir_modos(top_k)

    # conteo por tier
    counts = defaultdict(int)
    for p in qa:
        counts[p["_tier"]] += 1

    print("=" * 70)
    print(f"  PrivaceCheck — Ablation retriever estratificada por tier")
    print(f"  Total Q&A: {len(qa)}  |  top_k={top_k}")
    for t, label in TIER_LABEL.items():
        print(f"  {label}: {counts[t]} pares")
    print("=" * 70)

    resultados = {}
    for nombre, fn in modos.items():
        print(f"\nEvaluando: {nombre} ...")
        resultados[nombre] = evaluar_estratificado(fn, qa)

    # impresión por bucket
    _print_tabla("=== GLOBAL ===", resultados, "global", len(qa))
    for t, label in TIER_LABEL.items():
        _print_tabla(f"=== {label} ===", resultados, f"tier_{t}", counts[t])

    # delta híbrido vs emb por tier — el dato clave para la hipótesis del paper
    print("\n=== Delta MRR híbrido (emb+bm25) vs solo_embeddings, por tier ===")
    print(f"{'Tier':<35}{'emb':>8}{'híbrido':>10}{'Δ':>8}")
    print("-" * 61)
    hib = resultados["hibrido (emb+bm25)"]
    emb = resultados["solo_embeddings"]
    for bucket, label in (("global", "GLOBAL"),
                          ("tier_1", TIER_LABEL[1]),
                          ("tier_2", TIER_LABEL[2]),
                          ("tier_3", TIER_LABEL[3])):
        d_emb = emb[bucket]["MRR"]
        d_hib = hib[bucket]["MRR"]
        print(f"{label:<35}{d_emb:>8.3f}{d_hib:>10.3f}{d_hib - d_emb:>8.3f}")

    RESULTS_PATH.write_text(
        json.dumps(
            {
                "top_k": top_k,
                "n_total": len(qa),
                "n_por_tier": {f"tier_{t}": counts[t] for t in TIER_LABEL},
                "tier_map": TIER_MAP,
                "resultados": resultados,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nResultados guardados en: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
