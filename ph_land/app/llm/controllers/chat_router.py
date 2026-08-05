from fastapi import APIRouter

from app.llm.model.chat import ChatRequest, ChatResponse
from app.llm.core.llm import llm_service

chat_router = APIRouter()


@chat_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    answer = llm_service.ask(request.message)

    return ChatResponse(answer=answer)