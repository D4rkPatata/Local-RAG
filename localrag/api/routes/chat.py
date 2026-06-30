from fastapi import APIRouter, HTTPException, Cookie
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rag.retriever import chat_stream
from access import User, is_valid_role, ROLE_CLEARANCE
from auth import get_session

router = APIRouter()


class Mensaje(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    pregunta: str
    #role: str = "colaborador_general"
    history: list[Mensaje] = []


@router.post("/chat")
def chat(request: ChatRequest, session_token: str | None = Cookie(default=None)):
    # Autenticación via cookie
    if not session_token:
        raise HTTPException(status_code=401, detail="No autenticado.")
    user = get_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Sesión expirada.")

    history = [m.model_dump() for m in request.history]
    return StreamingResponse(
        chat_stream(request.pregunta, user=user, history=history),
        media_type="text/event-stream",
    )
