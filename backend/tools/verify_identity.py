from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Customer
from models.chat_session import IDENTITY_FIELD_KEYS


def _norm(value: Optional[str]) -> str:
    return (value or "").strip().casefold()


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
        if _norm(customer.phone_number) == _norm(
            collected_fields["phone_number"]
        ) and _norm(customer.address) == _norm(collected_fields["address"]):
            return customer
    return None
