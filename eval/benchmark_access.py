"""
benchmark_access.py — Evaluación del control de acceso por rol y tier.

Combina los Q&A base (Tier-1/2), Tier-3 y el set adversarial, itera sobre los 5
roles y mide:

  - Tier Leakage Rate (TLR): % de consultas de usuarios SIN clearance en las que
    información del documento prohibido alcanza la respuesta. Se mide en dos niveles:
      * retrieval-level (siempre): un chunk del doc prohibido llega al contexto.
        Es la garantía dura del filtro; no necesita LLM.
      * answer-level (si Ollama está arriba): el substring protegido aparece en la
        respuesta generada.
  - False Refusal Rate (FRR): % de consultas de usuarios CON clearance que el
    sistema rechaza indebidamente. (answer-level, requiere Ollama.)
  - Citation Accuracy: % de respuestas autorizadas que citan el doc_id correcto y
    cuyas citas corresponden a chunks efectivamente recuperados. (requiere Ollama.)
  - Adversarial Resilience: TLR sobre el set adversarial, desglosado por attack_type.

Uso:
    python eval/benchmark_access.py
"""
import re
import sys
import json
from pathlib import Path
from collections import defaultdict

import httpx

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "localrag"))

from access import User, ROLE_CLEARANCE, allowed_doc_ids, tier_of  # noqa: E402
from rag.vectorstore import retrieve  # noqa: E402
from rag.retriever import chat_stream, OPAQUE_REFUSAL, HONEST_REFUSAL  # noqa: E402
from config import settings  # noqa: E402

GT = ROOT / "corpus" / "ground_truth"
RESULTS_PATH = Path(__file__).parent / "results_access.json"
ROLES = list(ROLE_CLEARANCE)
CITE_RE = re.compile(r"\[(D\d{2})\]")
REFUSALS = {OPAQUE_REFUSAL, HONEST_REFUSAL}


def cargar_qa() -> list[dict]:
    """Une base + tier3 + adversarial, normalizando target_doc_id/target_tier/attack_type."""
    out = []
    for fname in ("nexus_qa_pairs.json", "nexus_qa_pairs_tier3.json", "nexus_qa_adversarial.json"):
        path = GT / fname
        if not path.exists():
            continue
        for p in json.loads(path.read_text(encoding="utf-8"))["qa_pairs"]:
            doc = p.get("target_doc_id", p["doc_id"])
            out.append({
                "id": p["id"],
                "question": p["question"],
                "answer": p["answer"],
                "target_doc_id": doc,
                "target_tier": p.get("target_tier", tier_of(doc)[0]),
                "attack_type": p.get("attack_type", "direct"),
            })
    return out


def ollama_disponible() -> bool:
    try:
        httpx.get(f"{settings.ollama_url}/api/tags", timeout=3)
        return True
    except Exception:
        return False


def responder(pregunta: str, user: User) -> str:
    return "".join(chat_stream(pregunta, user=user))


def evaluar(qa: list[dict], usar_llm: bool) -> dict:
    top_k = settings.top_k
    # acumuladores
    tlr_ctx = {"leak": 0, "n": 0}          # retrieval-level, todos los no-autorizados
    tlr_ans = {"leak": 0, "n": 0}          # answer-level (si LLM)
    frr = {"refuse": 0, "n": 0}            # autorizados no-adversariales
    cite = {"ok": 0, "n": 0}              # autorizados respondidos
    adv = defaultdict(lambda: {"leak": 0, "n": 0})  # por attack_type (retrieval-level)

    for par in qa:
        target = par["target_doc_id"]
        ans = par["answer"].lower()
        es_adv = par["attack_type"] != "direct"
        for role in ROLES:
            user = User("anon", role)
            autorizado = target in allowed_doc_ids(user)
            recuperado = retrieve(par["question"], mode="hibrido", top_k=top_k, user=user)
            ctx = " ".join(c["texto"] for c in recuperado).lower()
            doc_ids_ctx = {c["metadata"]["doc_id"] for c in recuperado}

            if not autorizado:
                # leak retrieval-level: ¿llegó un chunk del doc prohibido al contexto?
                leak_ctx = target in doc_ids_ctx
                tlr_ctx["n"] += 1
                tlr_ctx["leak"] += int(leak_ctx)
                if es_adv:
                    adv[par["attack_type"]]["n"] += 1
                    adv[par["attack_type"]]["leak"] += int(leak_ctx)

            if usar_llm:
                texto = responder(par["question"], user)
                low = texto.lower()
                if not autorizado:
                    tlr_ans["n"] += 1
                    tlr_ans["leak"] += int(ans in low)
                else:
                    refuso = texto.strip() in REFUSALS
                    if not es_adv:
                        frr["n"] += 1
                        frr["refuse"] += int(refuso)
                    if not refuso:
                        citados = set(CITE_RE.findall(texto))
                        cite["n"] += 1
                        # cita correcta: incluye el doc objetivo y no inventa fuera del contexto
                        ok = target in citados and citados.issubset(doc_ids_ctx)
                        cite["ok"] += int(ok)

    def rate(d, num, den="n"):
        return (d[num] / d[den]) if d[den] else 0.0

    res = {
        "tlr_retrieval": {"rate": rate(tlr_ctx, "leak"), **tlr_ctx},
        "adversarial_resilience": {
            atk: {"tlr_retrieval": rate(v, "leak"), **v} for atk, v in adv.items()
        },
    }
    if usar_llm:
        res["tlr_answer"] = {"rate": rate(tlr_ans, "leak"), **tlr_ans}
        res["false_refusal_rate"] = {"rate": rate(frr, "refuse"), **frr}
        res["citation_accuracy"] = {"rate": rate(cite, "ok"), **cite}
    return res


def main() -> None:
    qa = cargar_qa()
    usar_llm = ollama_disponible()
    print("=" * 64)
    print(f"  PrivaceCheck — Benchmark de control de acceso")
    print(f"  Q&A: {len(qa)} | roles: {len(ROLES)} | refusal_mode={settings.refusal_mode}")
    print(f"  Modo: {'completo (Ollama disponible)' if usar_llm else 'retrieval-only (sin Ollama)'}")
    print("=" * 64)

    res = evaluar(qa, usar_llm)

    print(f"\nTier Leakage Rate (retrieval-level): {res['tlr_retrieval']['rate']:.1%} "
          f"({res['tlr_retrieval']['leak']}/{res['tlr_retrieval']['n']} consultas sin clearance)")
    print("\nAdversarial Resilience (TLR retrieval-level por attack_type):")
    for atk, v in sorted(res["adversarial_resilience"].items()):
        print(f"  {atk:<12} {v['tlr_retrieval']:.1%}  ({v['leak']}/{v['n']})")

    if usar_llm:
        print(f"\nTLR (answer-level):     {res['tlr_answer']['rate']:.1%} "
              f"({res['tlr_answer']['leak']}/{res['tlr_answer']['n']})")
        print(f"False Refusal Rate:     {res['false_refusal_rate']['rate']:.1%} "
              f"({res['false_refusal_rate']['refuse']}/{res['false_refusal_rate']['n']})")
        print(f"Citation Accuracy:      {res['citation_accuracy']['rate']:.1%} "
              f"({res['citation_accuracy']['ok']}/{res['citation_accuracy']['n']})")
    else:
        print("\n(FRR, TLR answer-level y Citation Accuracy requieren Ollama; "
              "corre de nuevo con el servidor arriba.)")

    RESULTS_PATH.write_text(
        json.dumps({"n_qa": len(qa), "roles": ROLES, "usar_llm": usar_llm,
                    "refusal_mode": settings.refusal_mode, "resultados": res},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n✓ Resultados guardados en: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
