import datetime
from typing import Literal

from models import ChatSession

MAX_ATTEMPTS = 3

CheckResult = Literal["ok", "wrong", "expired", "locked", "no_code"]


def check_verification_code(session: ChatSession, submitted_code: str) -> CheckResult:
    """Epic C3/C4's retry-and-expiry policy, enforced server-side.

    Does not mutate session.state — the caller decides what state to
    transition to for each result, since that also drives what gets written
    to the transcript.
    """
    if not session.verification_code or not session.code_expires_at:
        return "no_code"
    if datetime.datetime.utcnow() > session.code_expires_at:
        return "expired"
    if session.code_attempts >= MAX_ATTEMPTS:
        return "locked"
    if submitted_code.strip() == session.verification_code:
        return "ok"

    session.code_attempts += 1
    return "locked" if session.code_attempts >= MAX_ATTEMPTS else "wrong"
