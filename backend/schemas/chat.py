from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    # Bounds a malformed/huge payload before it reaches the LLM call or the
    # transcript JSONB column (Week 5 edge-case pass) — 4000 chars is well
    # beyond anything a real chat message needs.
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    session_id: UUID
    reply: str
    state: str
    timestamp: datetime
    # First name only, and only once known — lets the frontend personalize
    # the escalation greeting (Epic G2) without exposing the rest of
    # collected_fields/customer over the wire.
    known_first_name: Optional[str] = None
