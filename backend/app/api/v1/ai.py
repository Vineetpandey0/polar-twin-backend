from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel
from app.ai.assistant import ai_assistant

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    station_id: Optional[str] = "maitri"


@router.post("/chat")
async def ai_chat_endpoint(req: ChatRequest) -> dict:
    reply = await ai_assistant.chat(req.messages, req.station_id or "maitri")
    return {"reply": reply, "simulated": True}
