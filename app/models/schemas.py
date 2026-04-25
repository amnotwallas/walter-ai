from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str # "user" o "assistant"
    content: str

class ChatRequest(BaseModel):
    query: Optional[str] = Field(None, min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, description="ID único para mantener el hilo de la conversación")
    action: Optional[str] = Field("chat", description="Acción a realizar: 'init' o 'chat'")
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
