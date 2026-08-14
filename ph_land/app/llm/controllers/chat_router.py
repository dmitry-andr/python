from typing import Optional
from fastapi import APIRouter, Cookie, Response

from app.llm.model.chat import ChatRequest, ChatResponse
from app.llm.core.llm_chat import llm_service

chat_router = APIRouter()


@chat_router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    response: Response,
    session_id: Optional[str] = Cookie(default=None),
):
    active_session_id = request.session_id or session_id
    llm_response = llm_service.ask(request.message, session_id=active_session_id)

    response.set_cookie(
        key="session_id",
        value=llm_response["session_id"],
        httponly=True,
        samesite="lax",
        path="/",
        max_age=60 * 60,  # 1 hour, tune as needed
    )

    return ChatResponse(
        answer=llm_response["answer"],
        session_id=llm_response["session_id"],
    )