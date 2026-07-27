import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from llm.ollama_client import chat as ollama_chat
from models import ChatSession
from schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

# Persona from docs/system-prompt.md — no gating/tools yet, so the model
# just chats. The gating constraints in that doc apply once Epics B/C/F land.
SYSTEM_PERSONA = (
    "You are the SecureShip support assistant. You help customers check on "
    "the status of their parcel shipments. You are friendly, concise, and "
    "get to the point. You do not have access to any real shipment lookup "
    "tools yet — if asked about a specific shipment, say so plainly rather "
    "than inventing tracking numbers or statuses."
)


@router.post("/chat", response_model=ChatResponse, operation_id="sendChatMessage")
def post_chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session = None
    if request.session_id is not None:
        session = db.get(ChatSession, request.session_id)
    if session is None:
        session = ChatSession(state="anonymous", transcript=[])
        db.add(session)

    now = datetime.datetime.utcnow()
    user_entry = {
        "role": "user",
        "content": request.message,
        "timestamp": now.isoformat(),
    }
    # Reassign (not .append) so SQLAlchemy detects the JSONB column changed.
    session.transcript = session.transcript + [user_entry]

    ollama_messages = [{"role": "system", "content": SYSTEM_PERSONA}] + [
        {"role": entry["role"], "content": entry["content"]}
        for entry in session.transcript
    ]
    reply_text = ollama_chat(ollama_messages)

    assistant_entry = {
        "role": "assistant",
        "content": reply_text,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    session.transcript = session.transcript + [assistant_entry]

    db.commit()
    db.refresh(session)

    return ChatResponse(
        session_id=session.id,
        reply=reply_text,
        state=session.state,
        timestamp=datetime.datetime.utcnow(),
    )
