import datetime
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

# Matches Section 4.4's enum: label_created | in_transit | out_for_delivery |
# delivered | exception. Not a Postgres ENUM type on purpose — keeping it a
# plain string keeps the schema easy to tweak without a migration tool.
SHIPMENT_STATUSES = (
    "label_created",
    "in_transit",
    "out_for_delivery",
    "delivered",
    "exception",
)


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    tracking_number: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    carrier: Mapped[str] = mapped_column(String, nullable=False)
    origin: Mapped[str] = mapped_column(String, nullable=False)
    destination: Mapped[str] = mapped_column(String, nullable=False)
    estimated_delivery: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    last_update: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
