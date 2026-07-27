import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

# Matches Section 6.2's state machine. Only "anonymous" is written today —
# the rest of these values belong to the identity-gating logic (Epics B/C).
SESSION_STATES = (
    "anonymous",
    "collecting_identity",
    "code_sent",
    "awaiting_code",
    "verified",
    "escalated_to_human",
)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    state: Mapped[str] = mapped_column(String, nullable=False, default="anonymous")
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )
    # Array of {role, content, timestamp, tool_calls?} objects (Section 4.6).
    transcript: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
