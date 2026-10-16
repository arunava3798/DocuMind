"""Chat endpoints: synchronous JSON answer and a streamed (SSE) variant."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from ..schemas.chat import ChatRequest, ChatResponse, SourceChunk
from ..services import chat_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    history = [m.model_dump() for m in request.history]
    answer, sources = chat_service.answer_question(request.question, history, request.k)
    return ChatResponse(answer=answer, sources=[SourceChunk(**s) for s in sources])


@router.post("/chat/stream")
def chat_stream(request: ChatRequest) -> EventSourceResponse:
    history = [m.model_dump() for m in request.history]
    answer, sources = chat_service.answer_question(request.question, history, request.k)

    async def event_generator():
        for word in answer.split(" "):
            yield {"event": "token", "data": word + " "}
            await asyncio.sleep(0.02)
        yield {"event": "sources", "data": json.dumps(sources)}
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_generator())
