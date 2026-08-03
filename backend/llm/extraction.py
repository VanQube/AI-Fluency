from llm.ollama_client import chat_json
from models.chat_session import IDENTITY_FIELD_KEYS

_EXTRACTION_SYSTEM_PROMPT = (
    "You extract identity fields from a customer support conversation. "
    "Read the conversation and output a JSON object with exactly these keys: "
    "first_name, last_name, phone_number, address. "
    "Use the value the customer stated for each field you can find, taken "
    "verbatim from their messages. If a field was not mentioned anywhere in "
    "the conversation, its value must be null. Do not guess, infer, or "
    "invent a value that wasn't actually stated. Output ONLY the JSON "
    "object, nothing else."
)


def extract_identity_fields(transcript: list[dict], known_fields: dict) -> dict:
    """Re-derives the four identity fields from the whole conversation each
    call, rather than diffing turn-by-turn — simpler, and self-correcting if
    the customer corrects an earlier value ("actually it's Main St, not
    Maple St"). Falls back to `known_fields` for any key the model doesn't
    return or returns as empty/null, so a bad extraction never erases a
    previously-collected value.
    """
    conversation_text = "\n".join(
        f"{entry['role']}: {entry['content']}"
        for entry in transcript
        if entry.get("role") in ("user", "assistant")
    )
    messages = [
        {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": conversation_text or "(no messages yet)"},
    ]
    extracted = chat_json(messages)

    merged = dict(known_fields or {})
    for key in IDENTITY_FIELD_KEYS:
        value = extracted.get(key)
        if isinstance(value, str) and value.strip():
            merged[key] = value.strip()
        elif key not in merged:
            merged[key] = None
    return merged
