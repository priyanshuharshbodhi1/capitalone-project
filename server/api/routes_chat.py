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
        print(f"🚀 Starting chat stream with {len(payload.messages)} messages")
        print(f"📝 Last message: {payload.messages[-1].content[:100] if payload.messages else 'No messages'}")
        print(f"🌍 Context: {payload.context}")
        
        # Ensure messages are dictionaries, not Pydantic models
        msgs = [m.model_dump() if isinstance(m, Message) else m for m in payload.messages]
        
        event_count = 0
        async for event in graph.run_stream(msgs, payload.context):
            event_count += 1
            print(f"📤 Event {event_count}: {event.get('type', 'unknown')} - {str(event)[:200]}")
            # Encode data to JSON string for SSE so clients can JSON.parse reliably
            yield {"event": event.get("type", "token"), "data": json.dumps(event, ensure_ascii=False)}
            
        print(f"✅ Stream completed with {event_count} events")
    except Exception as e:
        error_msg = f"Stream error: {str(e)}"
        print(f"❌ {error_msg}")
        yield {"event": "error", "data": json.dumps({"error": error_msg, "type": "stream_error"})}


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
    try:
        print(f"🎯 Complete chat request with {len(req.messages)} messages")
        print(f"📝 Last message: {req.messages[-1].content[:100] if req.messages else 'No messages'}")
        print(f"🌍 Context: {req.context}")
        
        graph = get_app_graph()
        msgs = [m.model_dump() if isinstance(m, Message) else m for m in req.messages]
        
        # Get the single final event
        async for event in graph.run_stream(msgs, req.context):
            print(f"📥 Complete event: {event.get('type', 'unknown')} - {str(event)[:200]}")
            if event.get("type") == "final":
                response = CompleteResponse(
                    text=event.get("text", ""),
                    intent=", ".join(event.get("intents", [])),
                    citations=event.get("citations", [])
                )
                print(f"✅ Complete response: {response}")
                return response
        
        # If no final event, return default response
        print("⚠️ No final event received, returning default response")
        return CompleteResponse(text="I apologize, but I couldn't process your request at the moment. Please try again.")
        
    except Exception as e:
        error_msg = f"Complete chat error: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
