import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from models import Package, Shipment
from models.shipment import SHIPMENT_STATUSES

logger = logging.getLogger("secureship.tools.lookup_shipments")

# Epic F's enforcement point for Week 3: the ONLY function that reads the
# shipments table for a chat session. `customer_id` is a required positional
# argument supplied by the caller (gating.py) from `session.customer_id` —
# the trusted, server-side value set once at Epic B/C verification, never
# from the model's tool-call arguments or any user-supplied field. This
# function does not accept a customer_id from an "arguments" dict on
# purpose, so there is no parameter here a prompt-injected model could ever
# overwrite (Epic F1/F2). If a caller doesn't have a verified customer_id,
# it must not call this function at all — see gating.py's guard.

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "lookup_shipments",
        "description": (
            "Look up the current customer's own shipments. Always scoped "
            "server-side to the verified customer for this session — this "
            "tool has no way to look up another customer's shipments, so "
            "don't bother asking for a customer id or account number."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": list(SHIPMENT_STATUSES),
                    "description": (
                        "Optional filter: only shipments in this status. Only "
                        "set this if the customer named a specific status "
                        "themselves (e.g. 'is it delivered yet'). For general "
                        "questions ('what's going on with my order', 'has it "
                        "shipped') leave this unset so all shipments are "
                        "considered — don't guess a status from vague phrasing."
                    ),
                },
                "tracking_number": {
                    "type": "string",
                    "description": (
                        "Optional filter: a specific tracking number the "
                        "customer mentioned, to look up just that shipment."
                    ),
                },
            },
            "required": [],
        },
    },
}


def lookup_shipments(
    db: Session,
    customer_id: uuid.UUID,
    status: Optional[str] = None,
    tracking_number: Optional[str] = None,
) -> list[dict]:
    """Returns shipments (with their packages) belonging to `customer_id`
    only. `status`/`tracking_number` narrow the results; they never widen
    scope beyond this customer no matter what's passed in, since the query
    always filters on `Shipment.customer_id == customer_id` first.
    """
    # Section 8's demo note: this line is what makes Epic F's enforcement
    # point demonstrable rather than just asserted — it fires every time,
    # scoped to customer_id, regardless of what the model asked for.
    logger.info(
        "lookup_shipments(customer_id=%s, status=%s, tracking_number=%s)",
        customer_id,
        status,
        tracking_number,
    )

    query = db.query(Shipment).filter(Shipment.customer_id == customer_id)
    if status:
        query = query.filter(Shipment.status == status)
    if tracking_number:
        query = query.filter(Shipment.tracking_number == tracking_number)

    results = []
    for shipment in query.all():
        packages = (
            db.query(Package).filter(Package.shipment_id == shipment.id).all()
        )
        results.append(
            {
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "carrier": shipment.carrier,
                "origin": shipment.origin,
                "destination": shipment.destination,
                "estimated_delivery": shipment.estimated_delivery.isoformat(),
                "last_update": shipment.last_update.isoformat(),
                "packages": [
                    {
                        "description": package.description,
                        "weight_kg": float(package.weight_kg),
                        "declared_value": float(package.declared_value),
                    }
                    for package in packages
                ],
            }
        )
    return results
