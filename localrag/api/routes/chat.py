from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rag.retriever import chat_stream
from access import User, is_valid_role, ROLE_CLEARANCE

router = APIRouter()


class Mensaje(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    pregunta: str
    role: str = "colaborador_general"
    history: list[Mensaje] = []


@router.post("/chat")
def chat(request: ChatRequest):
    if not is_valid_role(request.role):
        raise HTTPException(
            status_code=400,
            detail=f"Rol inválido: {request.role!r}. Roles válidos: {sorted(ROLE_CLEARANCE)}.",
        )
    user = User(name="anonymous", role=request.role)
    history = [m.model_dump() for m in request.history]
    return StreamingResponse(
        chat_stream(request.pregunta, user=user, history=history),
        media_type="text/event-stream",
    )
