"""
access.py — Control de acceso por rol y tier de sensibilidad.

Define qué documentos puede ver cada rol. Es la base del aporte central del
proyecto: el retriever filtra los chunks por clearance ANTES de pasarlos al LLM,
de modo que un usuario nunca recibe información de un tier para el que no tiene
autorización.

Tiers:
    Tier-1 (employee-facing):     D01-D08, D15.
    Tier-2 (operacional interno): D09-D14.
    Tier-3 (estratégico confid.): D16-D23, subdividido en categorías:
        comercial: D16, D17, D18, D22.
        tecnico:   D19, D20, D21, D23.
"""
from dataclasses import dataclass

# doc_id -> (tier, categoria). Para Tier-1/2 la categoría es "general".
DOC_TIER: dict[str, tuple[int, str]] = {
    # Tier-1 — employee-facing
    "D01": (1, "general"), "D02": (1, "general"), "D03": (1, "general"),
    "D04": (1, "general"), "D05": (1, "general"), "D06": (1, "general"),
    "D07": (1, "general"), "D08": (1, "general"), "D15": (1, "general"),
    # Tier-2 — operacional interno
    "D09": (2, "general"), "D10": (2, "general"), "D11": (2, "general"),
    "D12": (2, "general"), "D13": (2, "general"), "D14": (2, "general"),
    # Tier-3 — estratégico confidencial / comercial
    "D16": (3, "comercial"), "D17": (3, "comercial"),
    "D18": (3, "comercial"), "D22": (3, "comercial"),
    # Tier-3 — estratégico confidencial / técnico
    "D19": (3, "tecnico"), "D20": (3, "tecnico"),
    "D21": (3, "tecnico"), "D23": (3, "tecnico"),
}

# rol -> conjunto de pares (tier, categoria) permitidos. "*" = cualquier categoría.
ROLE_CLEARANCE: dict[str, set[tuple[int, str]]] = {
    "colaborador_general": {(1, "*")},
    "mando_medio": {(1, "*"), (2, "*")},
    "comercial_senior": {(1, "*"), (2, "*"), (3, "comercial")},
    "tecnico_senior": {(1, "*"), (2, "*"), (3, "tecnico")},
    "gerencia": {(1, "*"), (2, "*"), (3, "*")},
}

# Tier/categoría que se asume para un documento subido que no está en DOC_TIER.
DEFAULT_TIER = 1
DEFAULT_CATEGORY = "desconocido"


@dataclass(frozen=True)
class User:
    name: str
    role: str


def is_valid_role(role: str) -> bool:
    return role in ROLE_CLEARANCE


def tier_of(doc_id: str) -> tuple[int, str]:
    """(tier, categoria) de un doc_id; default Tier-1/desconocido si no está mapeado."""
    return DOC_TIER.get(doc_id, (DEFAULT_TIER, DEFAULT_CATEGORY))


def _clearance_permite(clearance: set[tuple[int, str]], tier: int, categoria: str) -> bool:
    for c_tier, c_cat in clearance:
        if c_tier == tier and (c_cat == "*" or c_cat == categoria):
            return True
    return False


def allowed_doc_ids(user: User) -> set[str]:
    """Conjunto de doc_ids que el usuario tiene autorización para ver."""
    clearance = ROLE_CLEARANCE.get(user.role, set())
    return {
        doc_id
        for doc_id, (tier, categoria) in DOC_TIER.items()
        if _clearance_permite(clearance, tier, categoria)
    }
