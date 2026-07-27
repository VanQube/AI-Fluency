"""Mock data seed script (Section 4.4 schema), backend/Postgres phase.

Generates >=25 customers and 40-60 shipments (with packages) directly into
Postgres via the backend's SQLAlchemy models, so frontend mocks and backend
data follow the same shape. Re-runnable: clears the three tables first, then
reseeds deterministically (seeded RNG) so runs are reproducible.

Run via: docker-compose exec backend python scripts/seed_data.py
(mounted into the backend container at /app/scripts — see docker-compose.yml)
"""

import random
import uuid
from datetime import datetime, timedelta

from db.session import SessionLocal, create_all_tables
from models import Customer, Package, Shipment

random.seed(20260127)

FIRST_NAMES = [
    "Ava", "Liam", "Noah", "Emma", "Olivia", "Ethan", "Mia", "Lucas", "Sofia",
    "Mason", "Isla", "Logan", "Zoe", "Elijah", "Layla", "James", "Grace",
    "Benjamin", "Chloe", "Henry", "Ella", "Jack", "Nora", "Leo", "Ivy",
    "Daniel", "Ruby", "Owen", "Hannah", "Samuel",
]

LAST_NAMES = [
    "Novak", "Bennett", "Carter", "Diaz", "Ellison", "Fischer", "Garner",
    "Hayes", "Ibarra", "Jansen", "Kowalski", "Lindqvist", "Moreau",
    "Nakamura", "Osei", "Petrov", "Quinn", "Reyes", "Sorensen", "Thibault",
    "Ueda", "Valdez", "Weber", "Yilmaz", "Zimmerman",
]

STREETS = [
    "Maple Street", "Oak Avenue", "Birch Lane", "Cedar Road", "Elm Court",
    "Harbor Drive", "Sunset Boulevard", "River Walk", "Grove Street",
    "Highland Avenue",
]

CITIES = [
    "Springfield, IL", "Austin, TX", "Portland, OR", "Berlin, DE",
    "Lyon, FR", "Utrecht, NL", "Krakow, PL", "Malmo, SE", "Denver, CO",
    "Raleigh, NC",
]

CARRIERS = ["MockExpress", "ParcelHawk", "SwiftCrate", "NorthLine Freight"]

STATUSES = (
    ["in_transit"] * 3
    + ["delivered"] * 3
    + ["out_for_delivery"] * 2
    + ["label_created"]
    + ["exception"]
)

PACKAGE_DESCRIPTIONS = [
    "Wireless earbuds", "Running shoes", "Ceramic mug set", "Paperback novel",
    "Phone case", "Desk lamp", "Yoga mat", "Board game", "Water bottle",
    "Bluetooth speaker", "Backpack", "Sunglasses",
]

REFERENCE_NOW = datetime(2026, 7, 27)


def generate_customers(count):
    customers = []
    for i in range(count):
        first_name = FIRST_NAMES[i % len(FIRST_NAMES)]
        last_name = random.choice(LAST_NAMES)
        customers.append(
            Customer(
                id=uuid.uuid4(),
                first_name=first_name,
                last_name=last_name,
                phone_number=(
                    f"+1{random.randint(200, 999)}{random.randint(100, 999)}"
                    f"{random.randint(1000, 9999)}"
                ),
                address=(
                    f"{random.randint(10, 9999)} {random.choice(STREETS)}, "
                    f"{random.choice(CITIES)}"
                ),
            )
        )
    return customers


def generate_shipments(customers, count):
    shipments = []
    for _ in range(count):
        customer = random.choice(customers)
        estimated_delivery = (
            REFERENCE_NOW + timedelta(days=random.randint(-10, 10))
        ).date()
        last_update = REFERENCE_NOW + timedelta(days=random.randint(-5, 5))
        shipments.append(
            Shipment(
                id=uuid.uuid4(),
                customer_id=customer.id,
                tracking_number=f"MX{random.randint(100000000, 999999999)}",
                status=random.choice(STATUSES),
                carrier=random.choice(CARRIERS),
                origin=random.choice(CITIES),
                destination=", ".join(customer.address.split(", ")[-2:]),
                estimated_delivery=estimated_delivery,
                last_update=last_update,
            )
        )
    return shipments


def generate_packages(shipments):
    packages = []
    for shipment in shipments:
        for _ in range(random.randint(1, 2)):
            packages.append(
                Package(
                    id=uuid.uuid4(),
                    shipment_id=shipment.id,
                    description=random.choice(PACKAGE_DESCRIPTIONS),
                    weight_kg=round(random.uniform(0.2, 5.0), 2),
                    declared_value=round(random.uniform(5.0, 250.0), 2),
                )
            )
    return packages


def main():
    create_all_tables()
    db = SessionLocal()
    try:
        db.query(Package).delete()
        db.query(Shipment).delete()
        db.query(Customer).delete()
        db.commit()

        customers = generate_customers(25)
        db.add_all(customers)
        db.flush()  # no relationship() configured between models, so flush
        # explicitly between tables to guarantee FK-safe insert order

        shipments = generate_shipments(customers, 50)
        db.add_all(shipments)
        db.flush()

        packages = generate_packages(shipments)
        db.add_all(packages)

        db.commit()
        print(
            f"Seeded {len(customers)} customers, {len(shipments)} shipments, "
            f"{len(packages)} packages."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
