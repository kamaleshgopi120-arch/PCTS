"""
backend/test_schemas.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 8
Automated Pydantic Schema and Edge Case Validation Test Suite
=============================================================================

This script verifies:
1. Valid payloads pass schema validation with status code 201.
2. Invalid payloads trigger HTTP 422 (Unprocessable Entity).
3. Specific edge cases from edge_case.md (EC-06, EC-10, EC-13, EC-15) are enforced.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_user_validation():
    print("\n[TEST SET 1] User Validation (UserCreate Schema)")
    print("-" * 70)

    # 1.1 Valid User Payload
    valid_payload = {
        "email": "student@pondiuni.ac.in",
        "password": "SecurePassword123",
        "role": "customer"
    }
    res = client.post("/demo/users/register", json=valid_payload)
    print(f">> 1.1 Valid Registration: HTTP {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}"
    assert res.json()["email"] == "student@pondiuni.ac.in"
    assert "password" not in res.json()  # Security: password must not be leaked

    # 1.2 Invalid Email Format
    invalid_email = {
        "email": "not-an-email-address",
        "password": "SecurePassword123",
        "role": "customer"
    }
    res = client.post("/demo/users/register", json=invalid_email)
    print(f">> 1.2 Invalid Email Format: HTTP {res.status_code} (Rejected)")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"

    # 1.3 Password Too Short (EC-06)
    short_pw = {
        "email": "valid@gmail.com",
        "password": "short",  # Less than 8 chars
        "role": "customer"
    }
    res = client.post("/demo/users/register", json=short_pw)
    print(f">> 1.3 Short Password (< 8 chars): HTTP {res.status_code} (Rejected - EC-06)")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"


def test_customer_validation():
    print("\n[TEST SET 2] Customer Validation (CustomerCreate Schema)")
    print("-" * 70)

    # 2.1 Valid Customer Payload
    valid_cust = {
        "user_id": 1,
        "full_name": "Arun Kumar",
        "phone": "9876543210",
        "address": "12, Anna Nagar",
        "city": "Chennai"
    }
    res = client.post("/demo/customers", json=valid_cust)
    print(f">> 2.1 Valid Customer Creation: HTTP {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}"
    assert res.json()["full_name"] == "Arun Kumar"

    # 2.2 Invalid Phone with Letters (EC-10)
    bad_phone_letters = {
        "user_id": 1,
        "full_name": "Arun Kumar",
        "phone": "98765PHONE",
        "city": "Chennai"
    }
    res = client.post("/demo/customers", json=bad_phone_letters)
    print(f">> 2.2 Invalid Phone (letters): HTTP {res.status_code} (Rejected - EC-10)")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"

    # 2.3 Invalid Phone Too Short (< 10 digits)
    bad_phone_short = {
        "user_id": 1,
        "full_name": "Arun Kumar",
        "phone": "12345",
        "city": "Chennai"
    }
    res = client.post("/demo/customers", json=bad_phone_short)
    print(f">> 2.3 Invalid Phone (< 10 digits): HTTP {res.status_code} (Rejected)")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"


def test_parcel_validation():
    print("\n[TEST SET 3] Parcel Validation (ParcelCreate Schema & Edge Cases)")
    print("-" * 70)

    # 3.1 Valid Parcel Booking (3.5 kg -> Rs. 105.00)
    valid_parcel = {
        "customer_id": 1,
        "sender_name": "Arun Kumar",
        "sender_phone": "9876543210",
        "receiver_name": "Priya Sharma",
        "receiver_phone": "9876543222",
        "source_city": "Chennai",
        "destination_city": "Bengaluru",
        "parcel_type": "Electronics",
        "weight_kg": 3.50,
        "description": "Electronic accessories"
    }
    res = client.post("/demo/parcels/book", json=valid_parcel)
    print(f">> 3.1 Valid Parcel Booking: HTTP {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}"
    data = res.json()
    print(f"   Generated Tracking ID: {data['tracking_id']}")
    print(f"   Calculated Charge:     Rs. {data['charge']:.2f}")
    assert data["charge"] == 105.00, f"Expected 105.00, got {data['charge']}"

    # 3.2 Weight <= 0 (EC-13)
    zero_weight = dict(valid_parcel, weight_kg=0.0)
    res = client.post("/demo/parcels/book", json=zero_weight)
    print(f">> 3.2 Weight = 0 kg: HTTP {res.status_code} (Rejected - EC-13)")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"

    # 3.3 Source and Destination Cities are the Same (EC-15)
    same_city = dict(valid_parcel, source_city="Chennai", destination_city="Chennai")
    res = client.post("/demo/parcels/book", json=same_city)
    print(f">> 3.3 Same Source & Destination City: HTTP {res.status_code} (Rejected - EC-15)")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"
    # Verify error message detail mentions cities
    error_text = str(res.json())
    assert "Source and destination cities cannot be the same" in error_text

    # 3.4 Missing Required Field (EC-12)
    missing_field = dict(valid_parcel)
    del missing_field["destination_city"]
    res = client.post("/demo/parcels/book", json=missing_field)
    print(f">> 3.4 Missing Destination City: HTTP {res.status_code} (Rejected - EC-12)")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"


if __name__ == "__main__":
    print("=" * 70)
    print("  RUNNING PHASE 8 PYDANTIC SCHEMA VALIDATION TESTS")
    print("=" * 70)
    test_user_validation()
    test_customer_validation()
    test_parcel_validation()
    print("\n" + "=" * 70)
    print("  ALL 9 VALIDATION & EDGE CASE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
