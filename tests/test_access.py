"""
test_access.py — Tests del control de acceso por rol y tier.

Requiere el corpus indexado (python scripts/reindex_nexus.py). No requiere Ollama:
los casos de refusal se prueban en el camino de "retrieval vacío" sin llamar al LLM.

    python -m pytest tests/test_access.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "localrag"))

from access import User, allowed_doc_ids  # noqa: E402
from config import settings  # noqa: E402
import rag.retriever as retriever  # noqa: E402
from rag.retriever import chat_stream, OPAQUE_REFUSAL, HONEST_REFUSAL  # noqa: E402
from rag.vectorstore import retrieve  # noqa: E402

PRICING_Q = "¿Cuál es la tarifa hora estándar en soles de un Desarrollador Senior en Nexus?"  # D16, Tier-3


def test_allowed_doc_ids_por_rol():
    esperado = {
        "colaborador_general": {"D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D15"},
        "mando_medio": {"D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D15",
                        "D09", "D10", "D11", "D12", "D13", "D14"},
        "comercial_senior": {"D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D15",
                             "D09", "D10", "D11", "D12", "D13", "D14", "D16", "D17", "D18", "D22"},
        "tecnico_senior": {"D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D15",
                           "D09", "D10", "D11", "D12", "D13", "D14", "D19", "D20", "D21", "D23"},
        "gerencia": {f"D{n:02d}" for n in range(1, 24)},
    }
    for role, docs in esperado.items():
        assert allowed_doc_ids(User("x", role)) == docs, role


def test_retrieve_filtra_por_tier():
    # colaborador_general NO debe recibir ningún chunk Tier-3 (p. ej. D16 pricing)
    res = retrieve(PRICING_Q, mode="hibrido", top_k=10, user=User("x", "colaborador_general"))
    tiers = {c["metadata"]["tier"] for c in res}
    assert 3 not in tiers
    assert all(c["metadata"]["doc_id"] not in {"D16", "D17", "D18", "D22"} for c in res)

    # comercial_senior SÍ debe poder llegar a D16
    res2 = retrieve(PRICING_Q, mode="hibrido", top_k=10, user=User("x", "comercial_senior"))
    assert any(c["metadata"]["doc_id"] == "D16" for c in res2)


def test_retrieve_sin_user_es_backward_compatible():
    sin_user = retrieve(PRICING_Q, mode="hibrido", top_k=10)
    explicito_none = retrieve(PRICING_Q, mode="hibrido", top_k=10, user=None)
    ids_a = [c["id"] for c in sin_user]
    ids_b = [c["id"] for c in explicito_none]
    assert ids_a == ids_b
    # sin filtro, un doc Tier-3 puede aparecer (no hay control de acceso)
    assert any(c["metadata"]["tier"] == 3 for c in sin_user)


def test_refusal_opaca_no_revela_existencia(monkeypatch):
    # Forzamos retrieval vacío (sin contexto autorizado) para ejercer el refusal
    # sin depender del LLM.
    monkeypatch.setattr(retriever, "retrieve", lambda *a, **k: [])
    settings.refusal_mode = "opaque"
    user = User("x", "colaborador_general")

    out_bloqueado = "".join(chat_stream("pregunta sobre pricing Tier-3", user=user))
    out_sin_info = "".join(chat_stream("pregunta sin respuesta en el corpus", user=user))

    # En modo opaco ambas refusals son idénticas → no revela que la info existe
    assert out_bloqueado == out_sin_info == OPAQUE_REFUSAL
    assert "acceso" not in out_bloqueado.lower()
    assert "clearance" not in out_bloqueado.lower()


def test_refusal_honesto_si_revela_existencia(monkeypatch):
    # En modo honesto, si la info existe (retrieval sin filtro no vacío) se admite.
    settings.refusal_mode = "honest"
    # filtrado vacío, pero sin filtro hay resultados → existe pero restringido
    def fake_retrieve(pregunta, mode="hibrido", top_k=None, user=None, **k):
        return [] if user is not None else [{"id": "D16_x_0", "texto": "...", "metadata": {"doc_id": "D16"}}]
    monkeypatch.setattr(retriever, "retrieve", fake_retrieve)

    out = "".join(chat_stream(PRICING_Q, user=User("x", "colaborador_general")))
    assert out == HONEST_REFUSAL
    settings.refusal_mode = "opaque"  # restaurar
