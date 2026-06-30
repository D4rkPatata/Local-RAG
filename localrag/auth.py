"""
auth.py — Sesiones en memoria para el modo servidor.
Token simple UUID -> {user, expires}. Sin DB, suficiente para uso académico.
"""
import uuid
from datetime import datetime, timedelta
from access import User

SESSION_TTL_HOURS = 8
_sessions: dict[str, dict] = {}  # token -> {user: User, expires: datetime}


def create_session(user: User) -> str:
    token = str(uuid.uuid4())
    _sessions[token] = {
        "user": user,
        "expires": datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
    }
    return token


def get_session(token: str) -> User | None:
    session = _sessions.get(token)
    if not session:
        return None
    if datetime.utcnow() > session["expires"]:
        _sessions.pop(token, None)
        return None
    return session["user"]


def delete_session(token: str):
    _sessions.pop(token, None)