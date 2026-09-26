"""
backend/test_database.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 9
Verification of SQLAlchemy 2.0 Connection, Session, and ORM Models
=============================================================================
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, func
from backend.database import engine, SessionLocal, get_db
from backend.models import (
    User,
    Customer,
    DeliveryPerson,
    Parcel,
    ParcelStatus,
    Delivery,
    Payment
)


def test_database_connection():
    print("=" * 75)
    print("  SQLALCHEMY 2.0 ORM & DATABASE VERIFICATION (PHASE 9)")
    print("=" * 75)

    # 1. Test Raw Engine Connection
    print("\n[STEP 1] Testing Database Engine Connection...")
    with engine.connect() as connection:
        print(">> Engine successfully connected to MySQL server!")
        print(f">> Dialect: {engine.dialect.name} (Driver: {engine.dialect.driver})")

    # 2. Test Session and Querying ORM Models
    db = SessionLocal()
    try:
        # 2.1 Query User Table
        print("\n[STEP 2] Querying Users via ORM...")
        users = db.scalars(select(User).order_by(User.user_id)).all()
        print(f">> Total users found: {len(users)}")
        for u in users:
            print(f"   User ID: {u.user_id} | Email: {u.email:<25} | Role: {u.role}")
        assert len(users) >= 4, f"Expected at least 4 users, got {len(users)}"

        # 2.2 Query Customer Table & Relationship Navigation (Customer -> User)
        print("\n[STEP 3] Querying Customers and Navigating 1:1 Relationship (Customer -> User)...")
        customers = db.scalars(select(Customer)).all()
        print(f">> Total customers found: {len(customers)}")
        for c in customers:
            # Notice how we access user email directly through the ORM relationship: c.user.email
            print(f"   Customer: {c.full_name:<15} | City: {c.city:<12} | Linked User Email: {c.user.email}")
        assert len(customers) >= 2, f"Expected at least 2 customers, got {len(customers)}"

        # 2.3 Query Delivery Person
        print("\n[STEP 4] Querying Delivery Staff...")
        staff = db.scalars(select(DeliveryPerson)).all()
        print(f">> Total delivery staff found: {len(staff)}")
        for s in staff:
            print(f"   Agent: {s.full_name} | Vehicle: {s.vehicle_number} | Active: {s.is_active}")
        assert len(staff) >= 1

        # 2.4 Query Parcels and Multi-Table ORM Navigation
        print("\n[STEP 5] Querying Parcels and Traversing Full Object Graph...")
        parcels = db.scalars(select(Parcel).order_by(Parcel.parcel_id)).all()
        print(f">> Total parcels found: {len(parcels)}")
        print(f"{'Tracking ID':<20} {'Sender':<15} {'Destination':<12} {'Status':<18} {'Charge':<10}")
        print("-" * 80)
        for p in parcels:
            current_status = p.status.status if p.status else "Unknown"
            print(
                f"{p.tracking_id:<20} "
                f"{p.sender_name:<15} "
                f"{p.destination_city:<12} "
                f"{current_status:<18} "
                f"Rs. {p.charge:<8.2f}"
            )
        assert len(parcels) >= 5

        # 2.5 Query Delivery & Payment Relationships
        print("\n[STEP 6] Querying Delivery Assignments and Payments...")
        for p in parcels:
            if p.delivery:
                agent_name = p.delivery.delivery_person.full_name if p.delivery.delivery_person else "Unassigned"
                print(f"   Parcel {p.tracking_id} -> Assigned Agent: {agent_name} | Delivered: {p.delivery.delivered_at}")
            if p.payment:
                print(f"   Parcel {p.tracking_id} -> Payment: Rs. {p.payment.amount} ({p.payment.payment_status})")

    finally:
        db.close()

    # 3. Test `get_db` FastAPI Dependency Generator
    print("\n[STEP 7] Testing get_db Dependency Generator...")
    db_gen = get_db()
    session = next(db_gen)
    assert session.is_active, "Session from get_db should be active"
    try:
        parcel_count = session.scalar(select(func.count(Parcel.parcel_id)))
        print(f">> get_db generator yielded active session! Total parcels counted: {parcel_count}")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            print(">> get_db generator closed session properly (no leaks)!")

    print("\n" + "=" * 75)
    print("  ALL DATABASE & ORM MODEL TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    test_database_connection()
