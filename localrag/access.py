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

# doc_id -> nombre legible del documento (para citar por nombre, no por código).
DOC_TITLES: dict[str, str] = {
    "D01": "Manual de Bienvenida",
    "D02": "Procedimiento de Onboarding",
    "D03": "Política de Vacaciones y Licencias",
    "D04": "Política de Trabajo Remoto",
    "D05": "Evaluación de Desempeño",
    "D06": "Código de Conducta y Ética",
    "D07": "Plan de Capacitación",
    "D08": "Reglamento de Seguridad y Salud en el Trabajo",
    "D09": "Política de Seguridad de TI",
    "D10": "Gestión de Incidentes de TI",
    "D11": "Protección de Datos de Clientes",
    "D12": "Compras y Proveedores",
    "D13": "Gastos, Viáticos y Reembolsos",
    "D14": "Reglamento de Instalaciones",
    "D15": "Directorio y Organigrama",
    "D16": "Modelo de Pricing y Tarifario",
    "D17": "Playbook de Propuestas y RFP",
    "D18": "Cartera de Clientes y Contratos",
    "D19": "Arquitecturas de Referencia (ADRs)",
    "D20": "Post-Mortems y Lessons Learned",
    "D21": "Runbook de Delivery / SDLC",
    "D22": "Incidentes con Cliente y SLA",
    "D23": "Política de Uso de IA y LLMs",
}


def doc_title(doc_id: str) -> str:
    """Nombre legible del documento; cae al doc_id si no está mapeado."""
    return DOC_TITLES.get(doc_id, doc_id)


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
    admin: bool = False  # capacidad de administración del sistema (ortogonal al rol)


def is_valid_role(role: str) -> bool:
    return role in ROLE_CLEARANCE


def is_admin(user: User) -> bool:
    """¿El usuario puede administrar el corpus (subir/borrar documentos)?

    Es una capacidad operativa SEPARADA de la clearance de lectura: gestionar el
    sistema (sysadmin) no es lo mismo que tener jerarquía de negocio. Por eso no
    se ata al rol `gerencia`, sino a un flag explícito.
    """
    return user.admin


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

import bcrypt

USERS_DB: dict[str, dict] = {
    "juan.perez":  {"password_hash": "$2b$12$2u597m2sB.cP.HK0y9XVZOzlkVn16/lZZetAY6rfr7ildGAP0PiHG", "rol": "colaborador_general"},
    "ana.gomez":   {"password_hash": "$2b$12$UskBvIOkwftFxDNOrtAxc.DzpkEW6djABmlrl8hr9Fq92x9yVW2S.", "rol": "mando_medio"},
    "carlos.vega": {"password_hash": "$2b$12$EyUlL6JgEww6P6WYZTkcQ.QsCYvtrY9kFx8uFgyZoGi4LkgrhVXqm", "rol": "comercial_senior"},
    "lucia.rios":  {"password_hash": "$2b$12$WtKSyszGM1z/OdAANsBK5OxrpJt.fAk9JknC5HIspOi796IUOu6t6", "rol": "tecnico_senior"},
    # admin = sysadmin del sistema (puede gestionar el corpus). Flag separado del rol.
    "admin":       {"password_hash": "$2b$12$2ooKGLX0yjbg1OEbmN3.lOGf0dpuCQhnpw1ratj6xFqgHbS8esMIa", "rol": "gerencia", "admin": True},
}

def authenticate(username: str, password: str) -> "User | None":
    entry = USERS_DB.get(username)
    if not entry:
        return None
    if bcrypt.checkpw(password.encode(), entry["password_hash"].encode()):
        return User(name=username, role=entry["rol"], admin=entry.get("admin", False))
    return None
