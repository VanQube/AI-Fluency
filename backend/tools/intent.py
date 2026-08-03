import re

# Deliberately simple keyword heuristics, not an LLM call — these only ever
# decide whether the backend *starts* the identity gate (Epic B1) or the
# cosmetic escalation theater (Epic G1). Neither one grants access to
# anything by itself, so a false positive/negative here is a UX papercut,
# not a security gap; the real enforcement point stays the backend tool
# layer (Epic F), not intent detection.

_SHIPMENT_PATTERN = re.compile(
    r"\b(shipment|package|parcel|order|tracking|deliver(y|ed|ies)?|where('?s| is) my)\b",
    re.IGNORECASE,
)

_HUMAN_PATTERN = re.compile(
    r"\b(talk to (a |an )?(human|person|agent|someone|representative)|"
    r"speak (to|with) (a |an )?(human|person|agent|someone|representative)|"
    r"real (person|human)|customer service rep)\b",
    re.IGNORECASE,
)


def looks_like_shipment_question(message: str) -> bool:
    return bool(_SHIPMENT_PATTERN.search(message))


def looks_like_human_request(message: str) -> bool:
    return bool(_HUMAN_PATTERN.search(message))
