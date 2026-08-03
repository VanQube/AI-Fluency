from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str


class ChatResponse(BaseModel):
    session_id: UUID
    reply: str
    state: str
    timestamp: datetime
    # First name only, and only once known — lets the frontend personalize
    # the escalation greeting (Epic G2) without exposing the rest of
    # collected_fields/customer over the wire.
    known_first_name: Optional[str] = None
