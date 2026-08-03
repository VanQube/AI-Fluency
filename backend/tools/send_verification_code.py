import datetime
import logging
import random

from models import ChatSession

logger = logging.getLogger("secureship.mock_sms")

CODE_TTL_MINUTES = 10


def send_verification_code(session: ChatSession) -> str:
    """Mocked SMS (Section 4.4/Epic C1) — console/log only, no real carrier.

    Logs the code alone, not alongside the customer's collected identity
    fields, so a plaintext scan of the console never shows "name + address +
    phone + code" together in one line (Section 4.3's no-PII-in-logs habit).
    """
    code = f"{random.randint(0, 999999):06d}"
    session.verification_code = code
    session.code_expires_at = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=CODE_TTL_MINUTES
    )
    session.code_attempts = 0
    logger.info(
        "[MOCK SMS] session=%s code=%s (expires in %s min)",
        session.id,
        code,
        CODE_TTL_MINUTES,
    )
    return code
