from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rag.retriever import chat_stream

router = APIRouter()

class ChatRequest(BaseModel):
    pregunta: str

@router.post("/chat")
def chat(request: ChatRequest):
    return StreamingResponse(
        chat_stream(request.pregunta),
        media_type="text/event-stream"
    )