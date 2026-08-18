import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    address: str


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class ShipmentBase(BaseModel):
    customer_id: UUID
    tracking_number: str
    status: str
    carrier: str
    origin: str
    destination: str
    estimated_delivery: datetime.date
    last_update: datetime.datetime


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentUpdate(BaseModel):
    customer_id: Optional[UUID] = None
    tracking_number: Optional[str] = None
    status: Optional[str] = None
    carrier: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    estimated_delivery: Optional[datetime.date] = None
    last_update: Optional[datetime.datetime] = None


class ShipmentRead(ShipmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class PackageBase(BaseModel):
    shipment_id: UUID
    description: str
    weight_kg: Decimal
    declared_value: Decimal


class PackageCreate(PackageBase):
    pass


class PackageUpdate(BaseModel):
    shipment_id: Optional[UUID] = None
    description: Optional[str] = None
    weight_kg: Optional[Decimal] = None
    declared_value: Optional[Decimal] = None


class PackageRead(PackageBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
