"""Section 6.2's conversation/identity-gating state machine, orchestrated by
the backend (not the model) per this week's design call — see PROGRESS.md.
routes/chat.py and routes/verify.py both call into this module so the state
machine has exactly one implementation.

Every branch is a generator (Iterator[str]) so the LLM-generated paths can
stream token-by-token (Section 8 Week 2 follow-up on perceived latency) while
deterministic/templated paths just yield their one string — callers don't
need to know which kind of branch they got.
"""

import re
from typing import Iterator, Optional, Tuple

from sqlalchemy.orm import Session

from llm.extraction import extract_identity_fields
from llm.ollama_client import chat_stream as ollama_chat_stream
from models import ChatSession
from models.chat_session import IDENTITY_FIELD_KEYS
from tools import (
    MAX_ATTEMPTS,
    check_verification_code,
    looks_like_human_request,
    looks_like_shipment_question,
    send_verification_code,
    verify_identity,
)

SYSTEM_PERSONA = (
    "You are the SecureShip support assistant. You help customers check on "
    "the status of their parcel shipments. You are friendly, concise, and "
    "get to the point. You do not have any shipment lookup tools yet — if "
    "asked about a specific shipment, say so plainly rather than inventing "
    "tracking numbers or statuses. Never reveal or imply whether a "
    "customer/shipment record exists for someone who hasn't been verified — "
    "that decision is made by the backend, not you."
)

ESCALATION_AGENT_NAME = "Melany"

_CODE_ONLY_PATTERN = re.compile(r"^\s*(\d{6})\s*$")


def known_first_name(session: ChatSession) -> Optional[str]:
    return (session.collected_fields or {}).get("first_name")


def _llm_reply_stream(
    session: ChatSession, extra_system_note: Optional[str] = None
) -> Iterator[str]:
    persona = SYSTEM_PERSONA if not extra_system_note else f"{SYSTEM_PERSONA}\n\n{extra_system_note}"
    ollama_messages = [{"role": "system", "content": persona}] + [
        {"role": entry["role"], "content": entry["content"]}
        for entry in session.transcript
        if entry.get("role") in ("user", "assistant")
    ]
    yield from ollama_chat_stream(ollama_messages)


def _handle_anonymous(session: ChatSession, message: str) -> Iterator[str]:
    if looks_like_shipment_question(message):
        session.state = "collecting_identity"
        session.collected_fields = {}
        yield (
            "I can help with that — first I need to verify who you are. "
            "Could you give me your first and last name, your address, and "
            "your phone number?"
        )
        return
    yield from _llm_reply_stream(session)


def _handle_collecting_identity(
    db: Session, session: ChatSession, message: str
) -> Iterator[str]:
    was_rejected = session.state == "identity_rejected"
    if session.state in ("identity_rejected", "code_expired"):
        session.state = "collecting_identity"

    # Extraction isn't shown to the user, so it stays a blocking call even
    # on the streaming path — only the conversational reply below streams.
    previous_fields = dict(session.collected_fields or {})
    session.collected_fields = extract_identity_fields(session.transcript, previous_fields)

    missing = [key for key in IDENTITY_FIELD_KEYS if not session.collected_fields.get(key)]
    if missing:
        note = (
            "The customer is being identity-verified before any shipment "
            f"lookup is allowed. Still missing: {', '.join(missing)}. Ask "
            "for just the missing field(s), conversationally — don't "
            "re-ask for details already provided, and don't ask for "
            "anything beyond name/address/phone."
        )
        yield from _llm_reply_stream(session, extra_system_note=note)
        return

    customer = verify_identity(db, session.collected_fields)
    if customer is None:
        gave_no_new_info = session.collected_fields == previous_fields
        if was_rejected and gave_no_new_info:
            session.state = "anonymous"
            session.collected_fields = {}
            yield "No problem — let me know if there's anything else I can help with."
            return
        session.state = "identity_rejected"
        yield (
            "I couldn't verify those details against our records — could "
            "you double-check your name, address, and phone number and try "
            "again?"
        )
        return

    # Canonicalize to the matched DB record rather than what the customer
    # typed — otherwise a lowercase/typo'd "ava zimmerman" would carry
    # through into the verified-welcome and escalation greetings verbatim.
    session.collected_fields = {
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "phone_number": customer.phone_number,
        "address": customer.address,
    }
    session.pending_customer_id = customer.id
    send_verification_code(session)
    session.state = "awaiting_code"
    yield (
        f"Thanks, {customer.first_name}! I've sent a 6-digit verification "
        "code to the phone number on file — enter it below to continue."
    )


def process_code_submission(session: ChatSession, submitted_code: str) -> Tuple[bool, str]:
    """Shared by the /verify-code endpoint and a bare 6-digit code typed
    straight into chat. Mutates session state/fields; does not touch the
    transcript or commit — callers own that. Not a streaming path — code
    checking is a fast deterministic lookup, not an LLM call.
    """
    result = check_verification_code(session, submitted_code)

    if result == "ok":
        session.customer_id = session.pending_customer_id
        session.pending_customer_id = None
        session.verification_code = None
        session.code_expires_at = None
        session.state = "verified"
        name = known_first_name(session) or "there"
        return True, f"Verified — welcome back, {name}! What can I help you with?"

    if result in ("expired", "locked"):
        session.state = "code_expired"
        session.verification_code = None
        session.code_expires_at = None
        reason = "expired" if result == "expired" else "too many incorrect attempts"
        return False, (
            f"That verification code is no longer valid ({reason}). Let's "
            "start over — go ahead and re-share your details."
        )

    if result == "wrong":
        remaining = MAX_ATTEMPTS - session.code_attempts
        return False, f"That code doesn't match — {remaining} attempt(s) left."

    return False, "There's no verification code pending for this session."


def _handle_awaiting_code_chat_message(session: ChatSession, message: str) -> Iterator[str]:
    match = _CODE_ONLY_PATTERN.match(message)
    if not match:
        yield (
            "I've sent a 6-digit code — enter it in the code box above (or "
            "just type the 6 digits here)."
        )
        return
    _, reply = process_code_submission(session, match.group(1))
    yield reply


def _handle_verified(session: ChatSession, message: str) -> Iterator[str]:
    note = (
        "This customer is verified, but there is still no shipment lookup "
        "tool available yet (that's Week 3 / Epic F) — say so plainly "
        "rather than inventing shipment details."
    )
    yield from _llm_reply_stream(session, extra_system_note=note)


def _handle_escalation_trigger(session: ChatSession) -> Iterator[str]:
    session.state = "escalated_to_human"
    name = known_first_name(session)
    greeting = f" {name}" if name else ""
    # Staged as separate paragraphs on purpose — the frontend reveals each
    # one with a short delay to approximate Section 6.2b's "scripted, timed
    # sequence" over a plain HTTP request/response (Section 6.3, not 6.3b).
    yield (
        "Thank you for your patience, switching you to a human.\n\n"
        f"{ESCALATION_AGENT_NAME} has entered the chat.\n\n"
        f"Hello, my name is {ESCALATION_AGENT_NAME}, let me just read through "
        "the chat...\n\n"
        f"Hey{greeting}, I'm up to speed, how can I help?"
    )


def _handle_escalated_chat(session: ChatSession, message: str) -> Iterator[str]:
    note = (
        f"You are now roleplaying as {ESCALATION_AGENT_NAME}, a human "
        "support agent — this is cosmetic UI theater only (Epic G3), there "
        "is no real human and no ticketing system. Stay in character. You "
        "still have no shipment lookup tools, so don't invent tracking "
        "info, and escalation does NOT bypass identity verification — "
        "don't reveal or imply whether any record exists for a customer "
        "who hasn't been verified (Epic G4)."
    )
    yield from _llm_reply_stream(session, extra_system_note=note)


def handle_turn_stream(db: Session, session: ChatSession, message: str) -> Iterator[str]:
    """Single entry point for routing one user message through the state
    machine. Epic G1: escalation is checked first, from any state, before
    the state-specific branches below. Yields the reply incrementally.
    """
    if session.state != "escalated_to_human" and looks_like_human_request(message):
        yield from _handle_escalation_trigger(session)
        return

    if session.state == "anonymous":
        yield from _handle_anonymous(session, message)
        return
    if session.state in ("collecting_identity", "identity_rejected", "code_expired"):
        yield from _handle_collecting_identity(db, session, message)
        return
    if session.state in ("code_sent", "awaiting_code"):
        yield from _handle_awaiting_code_chat_message(session, message)
        return
    if session.state == "verified":
        yield from _handle_verified(session, message)
        return
    if session.state == "escalated_to_human":
        yield from _handle_escalated_chat(session, message)
        return

    yield from _llm_reply_stream(session)


def handle_turn(db: Session, session: ChatSession, message: str) -> str:
    """Blocking convenience wrapper around handle_turn_stream, for the
    non-streaming /chat endpoint (curl-friendly, no SSE parsing needed).
    """
    return "".join(handle_turn_stream(db, session, message))
