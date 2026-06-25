"""
airgap.py — Endurecimiento offline / sin egreso a red pública.

Importar este módulo lo más temprano posible (antes de chromadb y de
sentence-transformers) fuerza modo offline y apaga TODA telemetría de las
librerías que podrían filtrar información hacia internet:

  - HuggingFace Hub / Transformers / sentence-transformers (descargas + telemetría)
  - ChromaDB (telemetría PostHog)

Por defecto el sistema arranca OFFLINE (LOCALRAG_OFFLINE=1). Para la descarga
inicial de modelos —una sola vez, con red— ejecutar con LOCALRAG_OFFLINE=0:

    LOCALRAG_OFFLINE=0 python scripts/reindex_nexus.py   # baja el modelo y cachea

Es idempotente: solo fija variables que no estén ya definidas en el entorno.
"""
import os

# Telemetría: siempre apagada. En un despliegue on-premise no hay motivo
# legítimo para que estas librerías "llamen a casa".
_TELEMETRY_OFF = {
    "HF_HUB_DISABLE_TELEMETRY": "1",       # HuggingFace Hub
    "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",   # no enviar token implícito
    "ANONYMIZED_TELEMETRY": "False",        # ChromaDB (PostHog)
}

# Modo offline duro: las librerías de modelos no intentan ninguna conexión.
_OFFLINE = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
}


def is_offline() -> bool:
    """True salvo que se pida explícitamente LOCALRAG_OFFLINE=0 (setup inicial)."""
    return os.environ.get("LOCALRAG_OFFLINE", "1") != "0"


def enforce() -> bool:
    """Fija las variables de entorno de endurecimiento. Devuelve si quedó offline."""
    for k, v in _TELEMETRY_OFF.items():
        os.environ.setdefault(k, v)
    offline = is_offline()
    if offline:
        for k, v in _OFFLINE.items():
            os.environ.setdefault(k, v)
    return offline


# Se aplica al importar el módulo.
OFFLINE = enforce()
