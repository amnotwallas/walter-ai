from fastapi import APIRouter, Depends, Security
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse
from app.services.agent_service import AgentService
from app.core.security import validate_api_key

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, dependencies=[Security(validate_api_key)])
async def chat(
    request: ChatRequest, 
    agent: AgentService = Depends()
):
    response = agent.get_response(request.query, request.history)
    return ChatResponse(response=response)

@router.post("/chat/stream", dependencies=[Security(validate_api_key)])
async def chat_stream(
    request: ChatRequest, 
    agent: AgentService = Depends()
):
    return StreamingResponse(
        agent.get_streaming_response(request.query, request.history),
        media_type="text/event-stream"
    )
