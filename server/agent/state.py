from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TurnMessage(BaseModel):
    role: str  # user | assistant | tool
    content: str


class ToolResult(BaseModel):
    name: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    ok: bool = True
    error: Optional[str] = None
    latency_ms: Optional[int] = None


class AgentState(BaseModel):
    messages: List[TurnMessage] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    intent: Optional[str] = None  # weather | market | general
    tools_used: List[ToolResult] = Field(default_factory=list)
    answer: Optional[str] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)

    def last_user(self) -> Optional[str]:
        for m in reversed(self.messages):
            if m.role == "user":
                return m.content
        return None
