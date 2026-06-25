"""
verify_airgap.py — Verificación de egreso cero (air-gap) del pipeline RAG.

Instala guardas sobre socket.connect y socket.getaddrinfo, ejecuta una carga de
trabajo representativa (cargar el modelo de embeddings + recuperar en los tres
modos) y reporta TODOS los intentos de salida a la red, clasificándolos en
loopback (permitido) vs externo (fuga). Sirve como evidencia reproducible para
el paper de que el sistema no filtra información a internet.

Cubre el proceso Python (embeddings, ChromaDB, LDA, BM25). El proceso Ollama es
independiente y se controla con firewall (ver docs/AIRGAP.md); su inferencia es
loopback (127.0.0.1:11434).

Uso:
    python scripts/verify_airgap.py
"""
import sys
import socket
import ipaddress
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "localrag"))

import airgap  # noqa: E402  — fuerza el modo offline que vamos a verificar

# --- Guardas de red ---------------------------------------------------------
_intentos: list[tuple[str, str]] = []  # (tipo, destino)
_real_connect = socket.socket.connect
_real_getaddrinfo = socket.getaddrinfo


def _es_loopback(host: str) -> bool:
    if host in ("localhost", ""):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False  # un hostname (p. ej. huggingface.co) = intento de salida


def _guard_connect(self, address):
    host = address[0] if isinstance(address, (tuple, list)) else str(address)
    _intentos.append(("connect", str(host)))
    return _real_connect(self, address)


def _guard_getaddrinfo(host, *args, **kwargs):
    _intentos.append(("dns", str(host)))
    return _real_getaddrinfo(host, *args, **kwargs)


def _check_control_acceso() -> bool:
    """Confirma que el filtro por tier bloquea chunks prohibidos. Devuelve si pasó."""
    from access import User
    from rag.vectorstore import retrieve

    # colaborador_general (Tier-1) consultando un dato de D16 (Tier-3 confidencial)
    pregunta = "¿Cuál es la tarifa hora de un Desarrollador Senior?"
    res = retrieve(pregunta, mode="hibrido", top_k=10, user=User("anon", "colaborador_general"))
    tier3 = [c["metadata"]["doc_id"] for c in res if c["metadata"]["tier"] == 3]

    print("\n" + "-" * 60)
    print("  Control de acceso por tier (filtro de retrieval)")
    print("-" * 60)
    if tier3:
        print(f"✗ FALLA: un colaborador_general recibió chunks Tier-3: {tier3}")
        return False
    print("✓ OK: colaborador_general NO recibe ningún chunk Tier-3 (filtro efectivo).")
    return True


def main() -> int:
    socket.socket.connect = _guard_connect
    socket.getaddrinfo = _guard_getaddrinfo
    try:
        # --- Carga de trabajo representativa del pipeline ------------------
        from rag.embedder import embed
        from rag.vectorstore import retrieve, MODES

        pregunta = "¿cuántos días de vacaciones tengo al año?"
        embed(pregunta)                       # carga el modelo (riesgo de descarga HF)
        for mode in MODES:
            retrieve(pregunta, mode=mode)     # chromadb + lda, todo local
        acceso_ok = _check_control_acceso()   # también local, sin red
    finally:
        socket.socket.connect = _real_connect
        socket.getaddrinfo = _real_getaddrinfo

    externos = sorted({t for tipo, t in _intentos if not _es_loopback(t)})
    loopback = sorted({t for tipo, t in _intentos if _es_loopback(t)})

    print("=" * 60)
    print("  PrivaceCheck — Verificación de air-gap (egreso cero)")
    print("=" * 60)
    print(f"\nModo offline forzado: {airgap.OFFLINE}")
    print(f"Intentos de red totales: {len(_intentos)}")
    print(f"  Loopback (permitido): {loopback or '—'}")
    print(f"  Externos (fugas):     {externos or '—'}")

    if externos:
        print("\n✗ FALLA: el pipeline intentó salir a la red pública:")
        for host in externos:
            print(f"    → {host}")
        print("\nRevisa caché de modelos y variables offline (ver docs/AIRGAP.md).")
        return 1

    print("\n✓ OK: cero egreso a red pública. El pipeline RAG opera air-gapped.")
    print("  (El proceso Ollama se controla aparte con firewall — docs/AIRGAP.md)")
    return 0 if acceso_ok else 1


if __name__ == "__main__":
    sys.exit(main())
