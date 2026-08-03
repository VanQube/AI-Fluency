import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

# Full Section 6.2 state machine, including the two transient states
# ("identity_rejected", "code_expired") that Week 1 hadn't wired up yet.
SESSION_STATES = (
    "anonymous",
    "collecting_identity",
    "identity_rejected",
    "code_sent",
    "awaiting_code",
    "code_expired",
    "verified",
    "escalated_to_human",
)

# Keys collected conversationally during Epic B, merged in as they're
# extracted from free text — independent of the ERD's Customer table.
IDENTITY_FIELD_KEYS = ("first_name", "last_name", "phone_number", "address")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Set ONLY once the session reaches "verified" (Section 6.4 ERD note) —
    # this is the real enforcement signal for gated data access (Epic F),
    # independent of what `state` displays afterward (e.g. once escalated).
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    # Candidate match found by verify_identity() while awaiting code entry —
    # promoted to customer_id only on successful verification.
    pending_customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    state: Mapped[str] = mapped_column(String, nullable=False, default="anonymous")
    # {"first_name": str|None, "last_name": str|None, "phone_number": str|None,
    # "address": str|None} — filled in incrementally during CollectingIdentity.
    collected_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    verification_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    code_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )
    code_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, nullable=True
    )
    # Array of {role, content, timestamp, tool_calls?} objects (Section 4.6).
    transcript: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
