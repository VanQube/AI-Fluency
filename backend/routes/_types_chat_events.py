"""Dummy, never-called endpoint whose sole job is exporting ChatStreamEvent
into the OpenAPI schema so Orval/openapi-typescript generates a plain TS
type for it (Section 4.8's pattern — SSE payloads have no backing REST
response for FastAPI to describe otherwise). The frontend imports the
generated type but calls POST /chat/stream directly via fetch, not this
route.
"""

from fastapi import APIRouter

from schemas.stream import ChatStreamEvent

router = APIRouter()


@router.post(
    "/_types/chat-stream-events",
    response_model=ChatStreamEvent,
    operation_id="chatStreamEventType",
    include_in_schema=True,
)
def _chat_stream_event_type() -> ChatStreamEvent:
    raise NotImplementedError("Type-export only endpoint — never actually called.")
