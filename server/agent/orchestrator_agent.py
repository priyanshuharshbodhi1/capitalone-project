from __future__ import annotations
import asyncio
from typing import Any, AsyncGenerator, Dict, List, Tuple

from .state import AgentState, TurnMessage
from .delegating_agent import route_intent
from .composer_agent import compose_answer
from .agents.weather_agent import fetch_weather
from .agents.market_agent import fetch_market
from .memory.checkpointer import RedisCheckpointer

_checkpointer = RedisCheckpointer()


class AppGraph:
    def __init__(self) -> None:
        pass

    async def run_stream(self, messages: List[Dict[str, Any]], context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        # Build state
        state = AgentState(messages=[TurnMessage(**m) for m in messages], context=context)
        user_text = state.last_user() or ""
        intents = route_intent(user_text, context)
        
        # For now, just return the detected intents as the response
        intents_text = ", ".join(intents)
        response_text = f"Detected intents: {intents_text}"
        
        yield {"type": "final", "text": response_text, "intents": intents}


def _chunk_text(s: str, n: int) -> List[str]:
    return [s[i : i + n] for i in range(0, len(s), n)] if s else []


_app_graph: AppGraph | None = None


def get_app_graph() -> AppGraph:
    global _app_graph
    if _app_graph is None:
        _app_graph = AppGraph()
    return _app_graph
