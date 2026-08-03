from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatStreamEvent(BaseModel):
    """Shape of each Server-Sent Event on POST /chat/stream. Exported to the
    frontend as a plain TS type via the dummy endpoint below (Section 4.8's
    pattern for payloads with no backing REST response — SSE, like WS, has
    no normal JSON response body for Orval/openapi-typescript to see).

    type == "token": `content` is the next text chunk to append.
    type == "done": the turn is finished — `reply` is the full assembled
      text, plus the same metadata ChatResponse would have carried.
    type == "error": streaming failed partway through (e.g. Ollama dropped
      the connection) — frontend shows its usual connection-trouble message.
    """

    type: Literal["token", "done", "error"]
    content: Optional[str] = None
    reply: Optional[str] = None
    session_id: Optional[UUID] = None
    state: Optional[str] = None
    known_first_name: Optional[str] = None
