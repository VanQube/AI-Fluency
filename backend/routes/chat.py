import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.session import SessionLocal, get_db
from gating import handle_turn, handle_turn_stream, known_first_name
from models import ChatSession
from schemas.chat import ChatRequest, ChatResponse
from schemas.stream import ChatStreamEvent

router = APIRouter()


def _append(session: ChatSession, role: str, content: str) -> None:
    entry = {
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    # Reassign (not .append) so SQLAlchemy detects the JSONB column changed.
    session.transcript = session.transcript + [entry]


def _get_or_create_session(db: Session, session_id: Optional[UUID]) -> ChatSession:
    session = None
    if session_id is not None:
        session = db.get(ChatSession, session_id)
    if session is None:
        session = ChatSession(state="anonymous", transcript=[], collected_fields={})
        db.add(session)
        db.flush()
    return session


@router.post("/chat", response_model=ChatResponse, operation_id="sendChatMessage")
def post_chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session = _get_or_create_session(db, request.session_id)
    _append(session, "user", request.message)

    reply_text = handle_turn(db, session, request.message)

    _append(session, "assistant", reply_text)

    db.commit()
    db.refresh(session)

    return ChatResponse(
        session_id=session.id,
        reply=reply_text,
        state=session.state,
        timestamp=datetime.datetime.utcnow(),
        known_first_name=known_first_name(session),
    )


def _sse(event: ChatStreamEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


# Not in the OpenAPI schema (like the WebSocket path in Section 6.3b) — SSE
# has no normal JSON response body to describe. The type frontend code
# imports comes from the dummy endpoint in routes/_types_chat_events.py
# (Section 4.8's pattern), not from this route.
@router.post("/chat/stream", operation_id="sendChatMessageStream", include_in_schema=False)
def post_chat_stream(request: ChatRequest) -> StreamingResponse:
    # NOT using Depends(get_db) here: FastAPI tears down yield-dependencies
    # as soon as this function *returns* the StreamingResponse object, which
    # happens well before the generator below actually finishes streaming —
    # that closed the session mid-stream ("Instance is not persistent within
    # this Session"). Managing the session's lifetime inside the generator
    # itself, closed in `finally`, ties it to the stream's actual lifetime.
    db = SessionLocal()
    session = _get_or_create_session(db, request.session_id)
    _append(session, "user", request.message)

    def event_generator():
        chunks: list[str] = []
        try:
            try:
                for chunk in handle_turn_stream(db, session, request.message):
                    chunks.append(chunk)
                    yield _sse(ChatStreamEvent(type="token", content=chunk))
            except Exception:
                db.rollback()
                yield _sse(ChatStreamEvent(type="error"))
                return

            full_reply = "".join(chunks)
            _append(session, "assistant", full_reply)
            db.commit()
            db.refresh(session)

            yield _sse(
                ChatStreamEvent(
                    type="done",
                    reply=full_reply,
                    session_id=session.id,
                    state=session.state,
                    known_first_name=known_first_name(session),
                )
            )
        finally:
            db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
