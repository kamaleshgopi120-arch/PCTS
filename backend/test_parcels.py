"""
backend/test_parcels.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 12
Automated Test Suite for Parcel Booking API, Tracking ID, and Atomic Transactions
=============================================================================
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.main import app
from backend.database import SessionLocal
from backend.models.user import User
from backend.models.customer import Customer
from backend.models.parcel import Parcel
from backend.security import create_access_token

client = TestClient(app)


def get_test_tokens():
    """Retrieves auth tokens for Admin and Customer accounts."""
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@pcts.com"))
        admin_token = create_access_token({"sub": admin.email, "user_id": admin.user_id, "role": "admin"})

        cust1 = db.scalar(select(User).where(User.email == "arun.kumar@gmail.com"))
        cust1_token = create_access_token({"sub": cust1.email, "user_id": cust1.user_id, "role": "customer"})

        cust2 = db.scalar(select(User).where(User.email == "priya.sharma@yahoo.com"))
        cust2_token = create_access_token({"sub": cust2.email, "user_id": cust2.user_id, "role": "customer"})

        return admin_token, cust1_token, cust2_token
    finally:
        db.close()


def test_parcel_booking(cust1_token, admin_token):
    print("\n[TEST SET 1] POST /api/parcels - Parcel Booking & Atomic Transactions")
    print("-" * 75)

    cust1_headers = {"Authorization": f"Bearer {cust1_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1.1 Customer 1 booking a 3.5 kg parcel (Tier: 1.01-5kg -> Rs. 30/kg = Rs. 105.00)
    booking_payload = {
        "sender_name": "Arun Kumar",
        "sender_phone": "9876543210",
        "receiver_name": "Divya Prakash",
        "receiver_phone": "9876549999",
        "source_city": "Chennai",
        "destination_city": "Coimbatore",
        "parcel_type": "Electronics",
        "weight_kg": 3.50,
        "description": "Mechanical Keyboard and Mouse"
    }

    res = client.post("/api/parcels", json=booking_payload, headers=cust1_headers)
    print(f">> 1.1 Customer Booking (3.50 kg): HTTP {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    parcel = res.json()
    print(f"   Generated Tracking ID: {parcel['tracking_id']}")
    print(f"   Calculated Charge:     Rs. {parcel['charge']:.2f}")
    print(f"   Initial Status:        {parcel['status']} at {parcel['location']}")
    print(f"   Initial Payment:       Rs. {parcel['payment_amount']} ({parcel['payment_status']})")

    assert parcel["tracking_id"].startswith("PCTS-")
    assert parcel["charge"] == 105.00
    assert parcel["status"] == "Booked"
    assert parcel["payment_status"] == "Pending"

    # Verify atomic multi-table persistence in MySQL
    db = SessionLocal()
    saved = db.scalar(select(Parcel).where(Parcel.tracking_id == parcel["tracking_id"]))
    assert saved is not None
    assert saved.status.status == "Booked"
    assert saved.payment.payment_status == "Pending"
    booked_parcel_id = saved.parcel_id
    db.close()
    print("   Verified atomic insert across parcel, parcel_status, and payment tables!")

    # 1.2 Edge Case EC-15: Same source and destination city
    bad_cities = dict(booking_payload, source_city="Chennai", destination_city="Chennai")
    res_same = client.post("/api/parcels", json=bad_cities, headers=cust1_headers)
    print(f">> 1.2 Same Source & Destination City (EC-15): HTTP {res_same.status_code} (Rejected)")
    assert res_same.status_code == 422

    # 1.3 Edge Case EC-13: Weight <= 0
    bad_weight = dict(booking_payload, weight_kg=0.0)
    res_zero = client.post("/api/parcels", json=bad_weight, headers=cust1_headers)
    print(f">> 1.3 Zero Weight (EC-13): HTTP {res_zero.status_code} (Rejected)")
    assert res_zero.status_code == 422

    # 1.4 Edge Case EC-17: Admin booking for non-existent customer ID
    admin_booking = dict(booking_payload, customer_id=99999)
    res_bad_cust = client.post("/api/parcels", json=admin_booking, headers=admin_headers)
    print(f">> 1.4 Admin Non-Existent Customer (EC-17): HTTP {res_bad_cust.status_code} (Rejected)")
    assert res_bad_cust.status_code == 400
    assert "Customer not found." in res_bad_cust.json()["detail"]

    return booked_parcel_id


def test_list_parcels(cust1_token, cust2_token, admin_token):
    print("\n[TEST SET 2] GET /api/parcels - Role-Based Listing & Filtering")
    print("-" * 75)

    cust1_headers = {"Authorization": f"Bearer {cust1_token}"}
    cust2_headers = {"Authorization": f"Bearer {cust2_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2.1 Customer 1 lists parcels (Should only see parcels where customer_id == 1)
    res_c1 = client.get("/api/parcels", headers=cust1_headers)
    print(f">> 2.1 Customer 1 Parcel List: HTTP {res_c1.status_code}")
    assert res_c1.status_code == 200
    c1_parcels = res_c1.json()
    for p in c1_parcels:
        assert p["customer_id"] == 1, "Customer 1 saw another customer's parcel!"
    print(f"   Customer 1 sees {len(c1_parcels)} parcels (all customer_id == 1)")

    # 2.2 Customer 2 lists parcels (Should only see parcels where customer_id == 2)
    res_c2 = client.get("/api/parcels", headers=cust2_headers)
    assert res_c2.status_code == 200
    c2_parcels = res_c2.json()
    for p in c2_parcels:
        assert p["customer_id"] == 2
    print(f">> 2.2 Customer 2 sees {len(c2_parcels)} parcels (all customer_id == 2)")

    # 2.3 Admin lists parcels (Sees all parcels across system)
    res_admin = client.get("/api/parcels", headers=admin_headers)
    assert res_admin.status_code == 200
    all_parcels = res_admin.json()
    assert len(all_parcels) >= len(c1_parcels) + len(c2_parcels)
    print(f">> 2.3 Admin sees {len(all_parcels)} total parcels across all customers")

    # 2.4 Filter parcels by destination city
    res_filter = client.get("/api/parcels?city=Bengaluru", headers=admin_headers)
    assert res_filter.status_code == 200
    filtered = res_filter.json()
    for p in filtered:
        assert "Bengaluru" in p["destination_city"]
    print(f">> 2.4 Filter (?city=Bengaluru): Found {len(filtered)} parcels")


def test_get_parcel_by_id(cust1_token, cust2_token, admin_token, new_parcel_id):
    print("\n[TEST SET 3] GET /api/parcels/{id} - Retrieval & Access Control")
    print("-" * 75)

    cust1_headers = {"Authorization": f"Bearer {cust1_token}"}
    cust2_headers = {"Authorization": f"Bearer {cust2_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3.1 Customer 1 views their newly booked parcel
    res_own = client.get(f"/api/parcels/{new_parcel_id}", headers=cust1_headers)
    print(f">> 3.1 Customer 1 Accessing Own Parcel ({new_parcel_id}): HTTP {res_own.status_code}")
    assert res_own.status_code == 200
    p = res_own.json()
    assert p["parcel_id"] == new_parcel_id
    assert p["customer_id"] == 1

    # 3.2 Customer 2 attempts to view Customer 1's parcel -> 403 Forbidden
    res_forbidden = client.get(f"/api/parcels/{new_parcel_id}", headers=cust2_headers)
    print(f">> 3.2 Customer 2 Accessing Customer 1's Parcel: HTTP {res_forbidden.status_code} (Forbidden)")
    assert res_forbidden.status_code == 403

    # 3.3 Admin views Customer 1's parcel -> 200 OK
    res_admin = client.get(f"/api/parcels/{new_parcel_id}", headers=admin_headers)
    print(f">> 3.3 Admin Accessing Parcel ({new_parcel_id}): HTTP {res_admin.status_code}")
    assert res_admin.status_code == 200

    # 3.4 Non-existent parcel ID -> 404 Not Found
    res_404 = client.get("/api/parcels/99999", headers=admin_headers)
    print(f">> 3.4 Non-Existent Parcel ID: HTTP {res_404.status_code} (Not Found)")
    assert res_404.status_code == 404


if __name__ == "__main__":
    print("=" * 75)
    print("  PHASE 12: PARCEL BOOKING API AUTOMATED TEST SUITE")
    print("=" * 75)
    admin_tok, c1_tok, c2_tok = get_test_tokens()
    new_pid = test_parcel_booking(c1_tok, admin_tok)
    test_list_parcels(c1_tok, c2_tok, admin_tok)
    test_get_parcel_by_id(c1_tok, c2_tok, admin_tok, new_pid)
    print("\n" + "=" * 75)
    print("  ALL PARCEL BOOKING, TRACKING ID, AND ATOMIC TRANSACTION TESTS PASSED!")
    print("=" * 75)
