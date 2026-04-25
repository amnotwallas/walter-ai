from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str # "user" o "assistant"
    content: str

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
