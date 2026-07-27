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
