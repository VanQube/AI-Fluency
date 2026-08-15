import re
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Customer
from models.chat_session import IDENTITY_FIELD_KEYS


def _norm(value: Optional[str]) -> str:
    # Collapse whitespace (incl. around commas) so "123 Main St,  Springfield,IL"
    # and "123 Main St, Springfield, IL" compare equal — customers won't type
    # punctuation/spacing identically to the seeded data, and that's not a
    # meaningful part of "did they give us the right address."
    collapsed = re.sub(r"\s*,\s*", ", ", (value or "").strip())
    collapsed = re.sub(r"\s+", " ", collapsed)
    return collapsed.casefold()


def _norm_phone(value: Optional[str]) -> str:
    # Compare on digits only, and ignore a leading US country code (1) on
    # whichever side has one — customers type "619-737-2097" or
    # "(619) 737-2097", never the "+16197372097" form we store, and a
    # legitimate match shouldn't hinge on punctuation or an optional "1".
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def verify_identity(db: Session, collected_fields: dict) -> Optional[Customer]:
    """Epic F's enforcement point starts here: this is the ONLY code path that
    turns a conversation into a matched Customer row. It never trusts an id
    supplied by the model/user — only the four fields collected during
    CollectingIdentity (Epic B), matched exactly (after normalization)
    against the Customer table.

    Requires all four fields to be present; returns None on any missing
    field or on no exact match (Epic B3 — the caller must not distinguish
    "no match" from "missing field" in what it tells the user).
    """
    if not all((collected_fields or {}).get(key) for key in IDENTITY_FIELD_KEYS):
        return None

    candidates = (
        db.query(Customer)
        .filter(
            func.lower(func.trim(Customer.first_name))
            == _norm(collected_fields["first_name"]),
            func.lower(func.trim(Customer.last_name))
            == _norm(collected_fields["last_name"]),
        )
        .all()
    )
    for customer in candidates:
        if _norm_phone(customer.phone_number) == _norm_phone(
            collected_fields["phone_number"]
        ) and _norm(customer.address) == _norm(collected_fields["address"]):
            return customer
    return None
