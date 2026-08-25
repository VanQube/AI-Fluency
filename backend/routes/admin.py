from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from admin_auth import require_admin
from db.session import get_db
from models import ChatSession, Customer, Package, Shipment
from schemas.admin import (
    ChatSessionDetail,
    ChatSessionSummary,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    PackageCreate,
    PackageRead,
    PackageUpdate,
    ShipmentCreate,
    ShipmentRead,
    ShipmentUpdate,
)

# Every route here is gated by require_admin (Epic E3) — real Auth0 JWT
# validation (signature/issuer/audience against the tenant's JWKS), see
# admin_auth.py.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _get_or_404(db: Session, model, record_id: UUID):
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return record


def _delete_or_409(db: Session, record) -> None:
    db.delete(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete {type(record).__name__} — other records still reference it",
        )


# --- Customers ---------------------------------------------------------

@router.get("/customers", response_model=List[CustomerRead], operation_id="listCustomers")
def list_customers(db: Session = Depends(get_db)) -> List[Customer]:
    return db.query(Customer).order_by(Customer.last_name, Customer.first_name).all()


@router.post("/customers", response_model=CustomerRead, status_code=201, operation_id="createCustomer")
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers/{customer_id}", response_model=CustomerRead, operation_id="getCustomer")
def get_customer(customer_id: UUID, db: Session = Depends(get_db)) -> Customer:
    return _get_or_404(db, Customer, customer_id)


@router.put("/customers/{customer_id}", response_model=CustomerRead, operation_id="updateCustomer")
def update_customer(customer_id: UUID, payload: CustomerUpdate, db: Session = Depends(get_db)) -> Customer:
    customer = _get_or_404(db, Customer, customer_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/customers/{customer_id}", status_code=204, operation_id="deleteCustomer")
def delete_customer(customer_id: UUID, db: Session = Depends(get_db)) -> None:
    customer = _get_or_404(db, Customer, customer_id)
    _delete_or_409(db, customer)


# --- Shipments -----------------------------------------------------------

@router.get("/shipments", response_model=List[ShipmentRead], operation_id="listShipments")
def list_shipments(db: Session = Depends(get_db)) -> List[Shipment]:
    return db.query(Shipment).order_by(Shipment.last_update.desc()).all()


@router.post("/shipments", response_model=ShipmentRead, status_code=201, operation_id="createShipment")
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)) -> Shipment:
    _get_or_404(db, Customer, payload.customer_id)
    shipment = Shipment(**payload.model_dump())
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


@router.get("/shipments/{shipment_id}", response_model=ShipmentRead, operation_id="getShipment")
def get_shipment(shipment_id: UUID, db: Session = Depends(get_db)) -> Shipment:
    return _get_or_404(db, Shipment, shipment_id)


@router.put("/shipments/{shipment_id}", response_model=ShipmentRead, operation_id="updateShipment")
def update_shipment(shipment_id: UUID, payload: ShipmentUpdate, db: Session = Depends(get_db)) -> Shipment:
    shipment = _get_or_404(db, Shipment, shipment_id)
    updates = payload.model_dump(exclude_unset=True)
    if "customer_id" in updates:
        _get_or_404(db, Customer, updates["customer_id"])
    for field, value in updates.items():
        setattr(shipment, field, value)
    db.commit()
    db.refresh(shipment)
    return shipment


@router.delete("/shipments/{shipment_id}", status_code=204, operation_id="deleteShipment")
def delete_shipment(shipment_id: UUID, db: Session = Depends(get_db)) -> None:
    shipment = _get_or_404(db, Shipment, shipment_id)
    _delete_or_409(db, shipment)


# --- Packages --------------------------------------------------------------

@router.get("/packages", response_model=List[PackageRead], operation_id="listPackages")
def list_packages(db: Session = Depends(get_db)) -> List[Package]:
    return db.query(Package).all()


@router.post("/packages", response_model=PackageRead, status_code=201, operation_id="createPackage")
def create_package(payload: PackageCreate, db: Session = Depends(get_db)) -> Package:
    _get_or_404(db, Shipment, payload.shipment_id)
    package = Package(**payload.model_dump())
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


@router.get("/packages/{package_id}", response_model=PackageRead, operation_id="getPackage")
def get_package(package_id: UUID, db: Session = Depends(get_db)) -> Package:
    return _get_or_404(db, Package, package_id)


@router.put("/packages/{package_id}", response_model=PackageRead, operation_id="updatePackage")
def update_package(package_id: UUID, payload: PackageUpdate, db: Session = Depends(get_db)) -> Package:
    package = _get_or_404(db, Package, package_id)
    updates = payload.model_dump(exclude_unset=True)
    if "shipment_id" in updates:
        _get_or_404(db, Shipment, updates["shipment_id"])
    for field, value in updates.items():
        setattr(package, field, value)
    db.commit()
    db.refresh(package)
    return package


@router.delete("/packages/{package_id}", status_code=204, operation_id="deletePackage")
def delete_package(package_id: UUID, db: Session = Depends(get_db)) -> None:
    package = _get_or_404(db, Package, package_id)
    db.delete(package)
    db.commit()


# --- Chat sessions (read-only, Week 5 stretch goal) -----------------------
# Displays what gating.py already wrote during real conversations — the
# escalation flag (state="escalated_to_human") and the gating-rejection
# states (identity_rejected, code_expired) are the interesting rows to
# pull up here, per Section 8's Week 5 plan.

@router.get("/chat-sessions", response_model=List[ChatSessionSummary], operation_id="listChatSessions")
def list_chat_sessions(db: Session = Depends(get_db)) -> List[ChatSession]:
    return db.query(ChatSession).order_by(ChatSession.started_at.desc()).all()


@router.get(
    "/chat-sessions/{session_id}", response_model=ChatSessionDetail, operation_id="getChatSession"
)
def get_chat_session(session_id: UUID, db: Session = Depends(get_db)) -> ChatSession:
    return _get_or_404(db, ChatSession, session_id)
