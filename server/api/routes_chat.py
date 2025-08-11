from datetime import datetime
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ..agent.orchestrator_agent import get_app_graph

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    context: Dict[str, Any] = Field(default_factory=dict)


async def stream_events(payload: ChatRequest) -> AsyncGenerator[dict, None]:
    graph = get_app_graph()
    try:
        # Ensure messages are dictionaries, not Pydantic models
        msgs = [m.model_dump() if isinstance(m, Message) else m for m in payload.messages]
        async for event in graph.run_stream(msgs, payload.context):
            # Encode data to JSON string for SSE so clients can JSON.parse reliably
            yield {"event": event.get("type", "token"), "data": json.dumps(event, ensure_ascii=False)}
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"error": str(e)})}


@router.post("/stream")
async def stream_chat(req: ChatRequest) -> EventSourceResponse:
    async def event_publisher() -> AsyncGenerator[dict, None]:
        async for e in stream_events(req):
            yield e
    return EventSourceResponse(
        event_publisher(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
        media_type="text/event-stream",
        ping=15000,
    )


class CompleteResponse(BaseModel):
    text: str
    intent: str | None = None
    citations: list[Any] = Field(default_factory=list)


@router.post("/complete")
async def complete_chat(req: ChatRequest) -> CompleteResponse:
    graph = get_app_graph()
    msgs = [m.model_dump() if isinstance(m, Message) else m for m in req.messages]
    
    # Get the single final event
    async for event in graph.run_stream(msgs, req.context):
        if event.get("type") == "final":
            return CompleteResponse(
                text=event.get("text", ""),
                intent=", ".join(event.get("intents", [])),
                citations=event.get("citations", [])
            )
