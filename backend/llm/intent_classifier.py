from llm.ollama_client import chat_json

# Replaces the old regex heuristics in tools/intent.py (see PROGRESS.md's
# Week 2 backlog note) — same chat_json structured-output pattern
# extraction.py uses for identity fields. Motivated by two incidents where
# fixed patterns missed a real phrasing entirely (a typo — "shipmemt" —
# dodging the shipment-keyword regex; "talk with a human" dodging a
# regex that only allowed "talk to"): a keyword list can only ever grow
# reactively, one missed phrasing at a time, while a classifier judges
# meaning instead of surface form. This only changes *routing* — which
# branch of gating.py's state machine handles the turn — never the actual
# security enforcement (tool scoping, the disclosure-scanning backstop),
# so a classifier miss degrades to exactly the same backstop a regex miss
# already did.
_INTENT_SYSTEM_PROMPT = (
    "You classify a single message from a customer chatting with a parcel "
    "shipment support assistant. Output a JSON object with exactly these "
    "boolean keys:\n"
    "wants_shipment_info: true if the message asks about a shipment, "
    "package, order, delivery, or tracking status in any way — including "
    "indirectly, with typos/misspellings, or by containing something that "
    "looks like a tracking number.\n"
    "gave_identity_info: true if the message is volunteering personal "
    "identifying details (a name, a mailing address, or a phone number) "
    "rather than asking a question.\n"
    "wants_human: true if the message is asking to be connected with, or "
    "escalated to, a real human/person/agent/representative instead of "
    "continuing with the assistant.\n"
    "A message can be true on more than one key, or none. Output ONLY the "
    "JSON object, nothing else."
)

_INTENT_KEYS = ("wants_shipment_info", "gave_identity_info", "wants_human")


def classify_intent(message: str) -> dict:
    """Returns all three routing signals from one Ollama call rather than
    three separate round-trips. Falls back to all-False on a parse failure
    (chat_json's documented behavior) — the same "nothing new detected"
    fallback extract_identity_fields relies on, appropriate here since a
    missed signal degrades to the existing backstop/re-prompt, not a leak.
    """
    messages = [
        {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]
    result = chat_json(messages)
    return {key: bool(result.get(key)) for key in _INTENT_KEYS}
