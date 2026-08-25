"""Section 6.2's conversation/identity-gating state machine, orchestrated by
the backend (not the model) per this week's design call — see PROGRESS.md.
routes/chat.py and routes/verify.py both call into this module so the state
machine has exactly one implementation.

Every branch is a generator (Iterator[str]) so the LLM-generated paths can
stream token-by-token (Section 8 Week 2 follow-up on perceived latency) while
deterministic/templated paths just yield their one string — callers don't
need to know which kind of branch they got.
"""

import json
import re
from typing import Iterator, Optional, Tuple

from sqlalchemy.orm import Session

from llm.extraction import extract_identity_fields
from llm.intent_classifier import classify_intent
from llm.ollama_client import chat_stream as ollama_chat_stream
from llm.ollama_client import chat_with_tools as ollama_chat_with_tools
from models import ChatSession
from models.chat_session import IDENTITY_FIELD_KEYS
from tools import (
    LOOKUP_SHIPMENTS_TOOL,
    MAX_ATTEMPTS,
    TRACKING_CODE_PATTERN,
    check_verification_code,
    lookup_shipments,
    send_verification_code,
    verify_identity,
)

SYSTEM_PERSONA = (
    "You are the SecureShip support assistant. You help customers check on "
    "the status of their parcel shipments. You are friendly, concise, and "
    "get to the point. When a verified customer asks about their shipments, "
    "use the lookup_shipments tool rather than guessing — never invent "
    "tracking numbers, statuses, or delivery dates. The tool is always "
    "scoped to the current customer by the backend; it has no customer-id "
    "parameter, so don't try to pass one. Never reveal or imply whether a "
    "customer/shipment record exists for someone who hasn't been verified — "
    "that decision is made by the backend, not you."
)

# Keys a tool-call's arguments are allowed to carry through to
# lookup_shipments(). Anything else the model includes (e.g. a hallucinated
# "customer_id") is dropped here, before the call — Epic F's enforcement
# point stays in the tool layer, but this is where a stray id would be
# stripped if a model ever tried to supply one.
_LOOKUP_SHIPMENTS_ALLOWED_ARGS = ("status", "tracking_number")

ESCALATION_AGENT_NAME = "Melany"

_CODE_ONLY_PATTERN = re.compile(r"^\s*(\d{6})\s*$")

# Epic A3's backstop: every branch below that talks to an unverified user
# (anonymous, mid-identity-collection, or escalated-but-never-verified)
# goes through the model with no tool access — the SYSTEM_PERSONA asks it
# not to invent shipment specifics, but Epic F's whole premise is that
# asking isn't enforcement (a local 8B model won't always comply, and the
# incident that motivated this file: "shipmemt" — a one-letter typo — was
# enough to slip past intent detection into free-form chat that then
# fabricated a full delivery status). This is the actual backend check:
# scan the generated reply itself for the shape of a shipment-status claim
# and swap in the standard decline if it looks like one, regardless of
# what the model intended to say.
_DECLINE_MESSAGE = (
    "I can't share shipment details until I've verified who you are — "
    "could you give me your first and last name, your address, and your "
    "phone number?"
)
_STATUS_DISCLOSURE_PHRASES = (
    "delivered",
    "in transit",
    "out for delivery",
    "label created",
    "en route",
    "on its way",
    "arriving",
    "arrival",
    "estimated delivery",
)


def _looks_like_shipment_disclosure(reply: str) -> bool:
    if TRACKING_CODE_PATTERN.search(reply):
        return True
    lowered = reply.lower()
    return any(phrase in lowered for phrase in _STATUS_DISCLOSURE_PHRASES)


def _guarded_unverified_reply_stream(
    session: ChatSession, extra_system_note: Optional[str] = None
) -> Iterator[str]:
    """Same as _llm_reply_stream, but buffers the full reply and swaps in
    the standard decline message if it looks like a shipment-status claim
    (see _looks_like_shipment_disclosure). Only used for states where the
    customer isn't verified — the verified path in _handle_verified has a
    real tool behind it and doesn't need this net. Buffering trades away
    incremental streaming for these branches, but their legitimate replies
    are short (a clarifying question or a decline), so the latency cost is
    small next to the leak this closes.
    """
    full_reply = "".join(_llm_reply_stream(session, extra_system_note))
    if _looks_like_shipment_disclosure(full_reply):
        yield _DECLINE_MESSAGE
        return
    yield full_reply


def known_first_name(session: ChatSession) -> Optional[str]:
    return (session.collected_fields or {}).get("first_name")


def _build_messages(
    session: ChatSession, extra_system_note: Optional[str] = None
) -> list[dict]:
    persona = SYSTEM_PERSONA if not extra_system_note else f"{SYSTEM_PERSONA}\n\n{extra_system_note}"
    return [{"role": "system", "content": persona}] + [
        {"role": entry["role"], "content": entry["content"]}
        for entry in session.transcript
        if entry.get("role") in ("user", "assistant")
    ]


def _llm_reply_stream(
    session: ChatSession, extra_system_note: Optional[str] = None
) -> Iterator[str]:
    yield from ollama_chat_stream(_build_messages(session, extra_system_note))


def _handle_anonymous(
    db: Session, session: ChatSession, message: str, intent: dict
) -> Iterator[str]:
    # Checked before the shipment-question branch: a customer who supplies
    # identity details unprompted (e.g. answering the assistant's own
    # free-form "I'll need your name, address, and phone number", which
    # carries no ship/track keyword of its own) needs to actually go
    # through extraction/verify_identity on this turn — not just get
    # re-prompted with the same canned ask, which is what looked like
    # "verification" in the incident this branch fixes: the message went
    # to the ungated LLM fallback below instead, which had nothing backing
    # its claim that anything had been verified.
    if intent["gave_identity_info"]:
        session.state = "collecting_identity"
        session.collected_fields = {}
        yield from _handle_collecting_identity(db, session, message, intent)
        return
    if intent["wants_shipment_info"]:
        session.state = "collecting_identity"
        session.collected_fields = {}
        yield (
            "I can help with that — first I need to verify who you are. "
            "Could you give me your first and last name, your address, and "
            "your phone number?"
        )
        return
    note = (
        "This visitor has NOT been identity-verified and you have no "
        "shipment lookup tool available in this branch of the "
        "conversation. If anything here reads as being about a shipment, "
        "package, order, or tracking number — even indirectly — decline "
        "and ask for their first/last name, address, and phone number "
        "instead of answering. Never state or imply a delivery status, "
        "carrier, or date."
    )
    yield from _guarded_unverified_reply_stream(session, extra_system_note=note)


def _handle_collecting_identity(
    db: Session, session: ChatSession, message: str, intent: dict
) -> Iterator[str]:
    # Covers both re-entry cases: a mismatch (identity_rejected) and an
    # expired/locked code (code_expired) — see was_unresolved's use below.
    was_unresolved = session.state in ("identity_rejected", "code_expired")
    if was_unresolved:
        session.state = "collecting_identity"

    # Epic A3's "give up mid-verification" path (Week 5 edge-case pass):
    # re-entering here after a mismatch or an expired code doesn't mean the
    # customer wants to keep trying. If this message isn't volunteering
    # identity info, don't silently re-run extraction/re-verify — for
    # code_expired specifically, collected_fields is already a full match
    # from before, so skipping this check meant ANY message here silently
    # re-verified and sent a brand-new code, ignoring whatever the customer
    # actually said (e.g. "never mind, what's your return policy?").
    # Release back to Anonymous instead, same as the mismatch give-up below.
    if was_unresolved and not intent["gave_identity_info"]:
        session.state = "anonymous"
        session.collected_fields = {}
        yield "No problem — let me know if there's anything else I can help with."
        return

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
        yield from _guarded_unverified_reply_stream(session, extra_system_note=note)
        return

    customer = verify_identity(db, session.collected_fields)
    if customer is None:
        # Defense in depth if the classifier's gave_identity_info missed:
        # still bail out on unchanged fields after a prior mismatch/expiry,
        # exactly as before this fix for the identity_rejected case.
        gave_no_new_info = session.collected_fields == previous_fields
        if was_unresolved and gave_no_new_info:
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


def _run_lookup_shipments_tool_call(db: Session, session: ChatSession, tool_call: dict) -> dict:
    """Executes one model-requested lookup_shipments call. This is Epic F's
    enforcement point in the tool-calling path: `session.customer_id` (set
    only once, at verification — see models/chat_session.py) is the sole
    source of the customer scope, never anything from `arguments` below.
    Any unrecognized argument key (e.g. a hallucinated "customer_id") is
    silently dropped rather than forwarded.

    Incident (2026-08-15, playthrough): a verified customer asked casually
    "has it shipped out yet" and the model guessed `status=label_created`
    to narrow the search — matching none of the customer's real shipments
    (all delivered/out_for_delivery). The tool correctly returned [], but
    the model then answered from that empty result anyway, stating a
    fabricated status as fact instead of reporting nothing matched. Same
    class of problem Epic F already solved for customer scoping: a filter
    the model invented shouldn't be trusted to have narrowed correctly
    either, so on an empty filtered result this re-queries unfiltered and
    hands back the customer's *real* shipments as the actual grounding —
    the model can now only fabricate a status that contradicts data
    that's sitting right there in front of it, not answer from nothing.
    """
    raw_arguments = tool_call.get("function", {}).get("arguments") or {}
    if isinstance(raw_arguments, str):
        try:
            raw_arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            raw_arguments = {}
    safe_kwargs = {
        key: raw_arguments[key]
        for key in _LOOKUP_SHIPMENTS_ALLOWED_ARGS
        if raw_arguments.get(key)
    }
    results = lookup_shipments(db, session.customer_id, **safe_kwargs)
    if not results and safe_kwargs:
        fallback_results = lookup_shipments(db, session.customer_id)
        return {
            "shipments": fallback_results,
            "note": (
                f"No shipments matched the requested filter {safe_kwargs!r} "
                "— 'shipments' above is the customer's complete, unfiltered "
                "list instead. Only describe shipments actually present in "
                "it. If none of them match what the customer asked about, "
                "say so plainly rather than guessing or inventing a status."
            ),
        }
    return {"shipments": results}


def _tool_backed_reply_stream(
    db: Session, session: ChatSession, extra_system_note: Optional[str] = None
) -> Iterator[str]:
    """Shared by _handle_verified and the escalated-but-already-verified
    branch of _handle_escalated_chat: the real, tool-backed reply path.
    Only ever called with session.customer_id already set — Epic F3's
    single enforcement point (_run_lookup_shipments_tool_call) is what
    actually scopes the data, this function just orchestrates the two-hop
    round-trip identically regardless of which persona is asking.
    """
    ollama_messages = _build_messages(session, extra_system_note)
    first_response = ollama_chat_with_tools(ollama_messages, [LOOKUP_SHIPMENTS_TOOL])
    tool_calls = first_response.get("tool_calls") or []

    if not tool_calls:
        yield first_response.get("content", "")
        return

    ollama_messages.append(
        {"role": "assistant", "content": first_response.get("content", ""), "tool_calls": tool_calls}
    )
    for tool_call in tool_calls:
        tool_result = _run_lookup_shipments_tool_call(db, session, tool_call)
        ollama_messages.append({"role": "tool", "content": json.dumps(tool_result)})

    # The frontend renders this reply as markdown with specific styling for
    # a numbered shipment list vs. nested per-package bullets (MessageBubble
    # .js) — asking for that exact shape here (rather than leaving format
    # to the model's judgment call each time) is what keeps replies looking
    # like the intended layout instead of occasionally free-form prose.
    ollama_messages.append(
        {
            "role": "system",
            "content": (
                "Format multi-field results as markdown: one numbered list "
                "item per shipment, with bold field labels (e.g. "
                "**Status:**). If a shipment has more than one package, "
                "list them as a nested bullet list under that shipment "
                "rather than inline. If there's only one shipment, plain "
                "prose is fine. Rephrase raw status values naturally "
                "('in_transit' -> 'In transit', 'out_for_delivery' -> 'Out "
                "for delivery') rather than echoing the field's raw form."
            ),
        }
    )
    yield from ollama_chat_stream(ollama_messages)


def _handle_verified(db: Session, session: ChatSession, message: str) -> Iterator[str]:
    # Fail closed: this branch only ever runs for state == "verified", which
    # is only reached via process_code_submission() promoting customer_id
    # from pending_customer_id — but the tool call is gated on the value
    # itself, not just the state string, as the single check that actually
    # matters (Epic F3).
    if session.customer_id is None:
        yield from _llm_reply_stream(session)
        return
    yield from _tool_backed_reply_stream(db, session)


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


def _handle_escalated_chat(db: Session, session: ChatSession, message: str) -> Iterator[str]:
    # Epic G4 only requires that escalation not become a backdoor around
    # verification for someone who was never verified — it says nothing
    # about downgrading a customer who escalates *after* verifying. So a
    # session with a real customer_id keeps the real lookup_shipments tool
    # (Melany playing level-2 support with an actual case file), while a
    # session that was never verified stays on the guarded, tool-less path.
    if session.customer_id is not None:
        note = (
            f"You are now roleplaying as {ESCALATION_AGENT_NAME}, a human "
            "support agent — this is cosmetic UI theater only (Epic G3), "
            "there is no real human and no ticketing system, but this "
            "customer IS genuinely verified, so use the lookup_shipments "
            "tool exactly as you would if you weren't roleplaying. Stay in "
            "character while doing it."
        )
        yield from _tool_backed_reply_stream(db, session, extra_system_note=note)
        return

    note = (
        f"You are now roleplaying as {ESCALATION_AGENT_NAME}, a human "
        "support agent — this is cosmetic UI theater only (Epic G3), there "
        "is no real human and no ticketing system. Stay in character. You "
        "still have no shipment lookup tools, so don't invent tracking "
        "info, and escalation does NOT bypass identity verification — "
        "don't reveal or imply whether any record exists for a customer "
        "who hasn't been verified (Epic G4)."
    )
    yield from _guarded_unverified_reply_stream(session, extra_system_note=note)


def handle_turn_stream(db: Session, session: ChatSession, message: str) -> Iterator[str]:
    """Single entry point for routing one user message through the state
    machine. Epic G1: escalation is checked first, from any state, before
    the state-specific branches below. Yields the reply incrementally.

    Routing signals (shipment question / identity info / human request) all
    come from one semantic classify_intent() call rather than three regex
    checks — see llm/intent_classifier.py. Skipped once already escalated,
    since none of the three signals change behavior from that state.
    """
    intent = (
        classify_intent(message)
        if session.state != "escalated_to_human"
        else {"wants_shipment_info": False, "gave_identity_info": False, "wants_human": False}
    )

    if session.state != "escalated_to_human" and intent["wants_human"]:
        yield from _handle_escalation_trigger(session)
        return

    if session.state == "anonymous":
        yield from _handle_anonymous(db, session, message, intent)
        return
    if session.state in ("collecting_identity", "identity_rejected", "code_expired"):
        yield from _handle_collecting_identity(db, session, message, intent)
        return
    if session.state in ("code_sent", "awaiting_code"):
        yield from _handle_awaiting_code_chat_message(session, message)
        return
    if session.state == "verified":
        yield from _handle_verified(db, session, message)
        return
    if session.state == "escalated_to_human":
        yield from _handle_escalated_chat(db, session, message)
        return

    yield from _llm_reply_stream(session)


def handle_turn(db: Session, session: ChatSession, message: str) -> str:
    """Blocking convenience wrapper around handle_turn_stream, for the
    non-streaming /chat endpoint (curl-friendly, no SSE parsing needed).
    """
    return "".join(handle_turn_stream(db, session, message))
