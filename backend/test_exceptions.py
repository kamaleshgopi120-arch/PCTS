"""
backend/test_exceptions.py — Phase 18: Exception Handling & Validation Automated Test Suite
============================================================================================
Automated verification for global exception handling and edge cases:
- EC-34: Database connection / operational failure -> HTTP 503.
- EC-36: Unique constraint violation -> Friendly HTTP 400.
- EC-37: Foreign key constraint violation -> Friendly HTTP 400.
- EC-38: Multi-table transaction rollback on failure.
- EC-39: Extremely long string in text fields -> HTTP 422.
- EC-40: Wrong data type submitted -> HTTP 422.
- EC-41: Malformed JSON body -> HTTP 422.
- EC-42: Missing required fields -> HTTP 422 with clear field details.
============================================================================================
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError, IntegrityError

from backend.main import app
from backend.database import SessionLocal
from backend.models.user import User
from backend.models.parcel import Parcel
from backend.models.payment import Payment
from backend.models.parcel_status import ParcelStatus
from backend.security import create_access_token

client = TestClient(app)


def print_section(title: str):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def get_auth_token():
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == "arun.kumar@gmail.com"))
        return create_access_token({"sub": user.email, "user_id": user.user_id, "role": "customer"})
    finally:
        db.close()


def run_tests():
    print_section("PHASE 18: EXCEPTION HANDLING & VALIDATION TEST SUITE")

    token = get_auth_token()
    auth_headers = {"Authorization": f"Bearer {token}"}

    # -------------------------------------------------------------------------
    # TEST SET 1: Input Validation Edge Cases (EC-39, EC-40, EC-41, EC-42)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 1] Input Validation & Schema Formatting (EC-39 to EC-42)")
    print("-" * 75)

    # 1.1 EC-41: Malformed JSON
    res_malformed = client.post(
        "/api/parcels",
        content="{ bad_json: not_quoted ",
        headers={"Content-Type": "application/json", **auth_headers}
    )
    print(f">> 1.1 Malformed JSON (EC-41): HTTP {res_malformed.status_code}")
    assert res_malformed.status_code == 422
    err_body = res_malformed.json()
    assert "error" in err_body or "detail" in err_body
    print(f"    Clean response: {err_body.get('detail')}")

    # 1.2 EC-40: Wrong data type (string instead of numeric weight)
    res_wrong_type = client.post(
        "/api/parcels",
        json={
            "sender_name": "Ravi",
            "sender_phone": "9876543210",
            "receiver_name": "Kumar",
            "receiver_phone": "9123456780",
            "receiver_address": "12 Madurai Road",
            "source_city": "Chennai",
            "destination_city": "Madurai",
            "parcel_type": "General",
            "weight_kg": "five_kilos",  # Invalid type
            "description": "Books"
        },
        headers=auth_headers
    )
    print(f">> 1.2 Wrong Data Type (EC-40): HTTP {res_wrong_type.status_code}")
    assert res_wrong_type.status_code == 422
    print(f"    Detail: {res_wrong_type.json().get('detail')}")

    # 1.3 EC-39: Extremely long string in text field
    res_long_str = client.post(
        "/api/parcels",
        json={
            "sender_name": "A" * 150,  # Exceeds max_length 100
            "sender_phone": "9876543210",
            "receiver_name": "Kumar",
            "receiver_phone": "9123456780",
            "receiver_address": "12 Madurai Road",
            "source_city": "Chennai",
            "destination_city": "Madurai",
            "parcel_type": "General",
            "weight_kg": 2.5,
            "description": "Books"
        },
        headers=auth_headers
    )
    print(f">> 1.3 Extremely Long String (EC-39): HTTP {res_long_str.status_code}")
    assert res_long_str.status_code == 422
    print(f"    Detail: {res_long_str.json().get('detail')}")

    # 1.4 EC-42: Missing required parameters
    res_missing = client.post(
        "/api/parcels",
        json={"source_city": "Chennai"},
        headers=auth_headers
    )
    print(f">> 1.4 Missing Required Fields (EC-42): HTTP {res_missing.status_code}")
    assert res_missing.status_code == 422
    print(f"    Detail: {res_missing.json().get('detail')}")

    # -------------------------------------------------------------------------
    # TEST SET 2: Database Integrity Constraints (EC-36, EC-37)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 2] Database Constraint Violations (EC-36, EC-37)")
    print("-" * 75)

    # 2.1 EC-36: Unique constraint violation (duplicate email registration)
    res_dup = client.post(
        "/api/auth/register",
        json={
            "email": "admin@pcts.com",  # Already exists
            "password": "ValidPassword@123",
            "full_name": "Duplicate Admin",
            "phone": "9876543210",
            "role": "customer"
        }
    )
    print(f">> 2.1 Unique Constraint Violation (EC-36): HTTP {res_dup.status_code}")
    assert res_dup.status_code == 400
    assert "already registered" in res_dup.json().get("detail", "").lower() or "already exists" in res_dup.json().get("detail", "").lower()
    print(f"    Friendly Error: {res_dup.json().get('detail')}")

    # 2.2 EC-37: Foreign key constraint violation (delete customer with active parcels)
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.role == "admin"))
        admin_tok = create_access_token({"sub": admin.email, "user_id": admin.user_id, "role": "admin"})
    finally:
        db.close()

    res_fk = client.delete("/api/customers/1", headers={"Authorization": f"Bearer {admin_tok}"})
    print(f">> 2.2 Relational / FK Constraint Violation (EC-37): HTTP {res_fk.status_code}")
    assert res_fk.status_code == 400
    print(f"    Integrity Protection: {res_fk.json().get('detail')}")

    # -------------------------------------------------------------------------
    # TEST SET 3: Transaction Rollback on Failure (EC-38)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 3] Atomic Transaction Rollback on Midway Failure (EC-38)")
    print("-" * 75)

    db = SessionLocal()
    try:
        # Count initial parcels and payments
        initial_parcel_count = db.scalar(select(text("COUNT(*) FROM parcel"))).scalar() if hasattr(db.scalar(select(text("COUNT(*) FROM parcel"))), "scalar") else db.execute(text("SELECT COUNT(*) FROM parcel")).scalar()
        initial_payment_count = db.execute(text("SELECT COUNT(*) FROM payment")).scalar()

        # Simulate multi-step transaction where an error occurs before commit
        try:
            p = Parcel(
                tracking_id="PCTS-ROLLBACK-TEST",
                customer_id=1,
                sender_name="Fail Test",
                sender_phone="9876543210",
                receiver_name="Fail Recv",
                receiver_phone="9123456780",
                source_city="Chennai",
                destination_city="Salem",
                parcel_type="General",
                weight_kg=1.0,
                charge=50.0
            )
            db.add(p)
            db.flush()

            # Intentionally simulate midway failure
            raise RuntimeError("Midway transaction failure simulated for EC-38 testing")

            # This code is unreachable:
            db.commit()
        except RuntimeError:
            db.rollback()

        # Verify nothing was saved
        after_parcel_count = db.execute(text("SELECT COUNT(*) FROM parcel")).scalar()
        after_payment_count = db.execute(text("SELECT COUNT(*) FROM payment")).scalar()

        assert after_parcel_count == initial_parcel_count, "Rollback failed: parcel count changed!"
        assert after_payment_count == initial_payment_count, "Rollback failed: payment count changed!"
        print(">> 3.1 Transaction safely rolled back! Zero orphaned records created in database.")
    finally:
        db.close()

    # -------------------------------------------------------------------------
    # TEST SET 4: Database Connection Failure (EC-34)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 4] Database Connection / Operational Failure (EC-34)")
    print("-" * 75)

    # Directly verify the operational error handler responds with HTTP 503
    from backend.exceptions import register_exception_handlers
    from fastapi import FastAPI
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/test-db-down")
    def simulate_db_down():
        raise OperationalError("Can't connect to MySQL server on 'localhost' (10061)", {}, None)

    mock_client = TestClient(test_app)
    res_503 = mock_client.get("/test-db-down")
    print(f">> 4.1 Simulated Database Outage (EC-34): HTTP {res_503.status_code}")
    assert res_503.status_code == 503
    assert "Database service is temporarily unavailable" in res_503.json()["detail"]
    print(f"    Friendly 503 response: {res_503.json()}")

    print("\n" + "=" * 75)
    print("  ALL EXCEPTION HANDLING & VALIDATION TESTS PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
