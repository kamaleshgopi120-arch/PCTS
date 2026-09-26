"""
backend/test_payments.py — Phase 16: Payment Management API Automated Test Suite
================================================================================
Automated verification for viewing payments, settling transactions, and edge cases
(EC-30, EC-31, EC-32, EC-33).
================================================================================
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
from backend.models.parcel import Parcel
from backend.models.payment import Payment
from backend.security import create_access_token
from backend.mongo import get_tracking_history

client = TestClient(app)


def print_section(title: str):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def get_test_tokens():
    """Retrieve verified JWT tokens for admin and customers."""
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@pcts.com"))
        admin_tok = create_access_token({"sub": admin.email, "user_id": admin.user_id, "role": "admin"})

        cust1 = db.scalar(select(User).where(User.email == "arun.kumar@gmail.com"))
        cust1_tok = create_access_token({"sub": cust1.email, "user_id": cust1.user_id, "role": "customer"})

        cust2 = db.scalar(select(User).where(User.email == "priya.sharma@yahoo.com"))
        cust2_tok = create_access_token({"sub": cust2.email, "user_id": cust2.user_id, "role": "customer"})

        return admin_tok, cust1_tok, cust2_tok
    finally:
        db.close()


def book_test_parcel(auth_headers: dict) -> tuple[int, str, float]:
    """Helper to book a fresh parcel with an initial pending payment."""
    payload = {
        "sender_name": "Payment Test Sender",
        "sender_phone": "9876543210",
        "receiver_name": "Payment Test Receiver",
        "receiver_phone": "9123456780",
        "source_city": "Chennai",
        "destination_city": "Tiruchirappalli",
        "parcel_type": "General",
        "weight_kg": 4.0,
        "description": "Payment test consignment"
    }
    res = client.post("/api/parcels", json=payload, headers=auth_headers)
    assert res.status_code == 201, f"Parcel booking failed: {res.text}"
    data = res.json()
    return data["parcel_id"], data["tracking_id"], data["charge"]


def run_tests():
    print_section("PHASE 16: PAYMENT MANAGEMENT API AUTOMATED TEST SUITE")

    admin_tok, cust1_tok, cust2_tok = get_test_tokens()
    auth_admin = {"Authorization": f"Bearer {admin_tok}"}
    auth_cust1 = {"Authorization": f"Bearer {cust1_tok}"}
    auth_cust2 = {"Authorization": f"Bearer {cust2_tok}"}

    # -------------------------------------------------------------------------
    # TEST SET 1: GET /api/payments/{parcel_id} & Permissions
    # -------------------------------------------------------------------------
    print("\n[TEST SET 1] GET /api/payments/{parcel_id} - Viewing Payment Details")
    print("-" * 75)

    # 1.1 Without token -> 401 Unauthorized
    res1 = client.get("/api/payments/1")
    print(f">> 1.1 Without Token: HTTP {res1.status_code}")
    assert res1.status_code == 401

    # 1.2 EC-32: Non-existent parcel ID -> 404 Not Found
    res_ec32 = client.get("/api/payments/99999", headers=auth_admin)
    print(f">> 1.2 Non-Existent Parcel (EC-32): HTTP {res_ec32.status_code} (Not Found)")
    assert res_ec32.status_code == 404
    assert "parcel not found" in res_ec32.json()["detail"].lower()

    # Book a new parcel by customer 1
    pid1, tid1, charge1 = book_test_parcel(auth_cust1)
    print(f">> Booked parcel #{pid1} ({tid1}) with charge Rs. {charge1}")

    # 1.3 Customer 1 views own payment -> 200 OK
    res_p1 = client.get(f"/api/payments/{pid1}", headers=auth_cust1)
    print(f">> 1.3 Customer 1 Viewing Own Payment: HTTP {res_p1.status_code}")
    assert res_p1.status_code == 200
    pay_data1 = res_p1.json()
    payment_id1 = pay_data1["payment_id"]
    assert pay_data1["amount"] == charge1
    assert pay_data1["payment_status"] == "Pending"
    assert pay_data1["tracking_id"] == tid1
    print(f"    Payment ID: #{payment_id1} | Amount: Rs. {pay_data1['amount']} | Status: {pay_data1['payment_status']}")

    # 1.4 Customer 2 attempting to view Customer 1's payment -> 403 Forbidden
    res_p2_unauth = client.get(f"/api/payments/{pid1}", headers=auth_cust2)
    print(f">> 1.4 Customer 2 Accessing Other Customer's Payment: HTTP {res_p2_unauth.status_code} (Forbidden)")
    assert res_p2_unauth.status_code == 403

    # 1.5 Admin viewing Customer 1's payment -> 200 OK
    res_admin_view = client.get(f"/api/payments/{pid1}", headers=auth_admin)
    print(f">> 1.5 Admin Viewing Payment: HTTP {res_admin_view.status_code}")
    assert res_admin_view.status_code == 200

    # -------------------------------------------------------------------------
    # TEST SET 2: GET /api/payments/id/{payment_id}
    # -------------------------------------------------------------------------
    print("\n[TEST SET 2] GET /api/payments/id/{payment_id} - Direct ID Lookup")
    print("-" * 75)

    # 2.1 EC-33: Non-existent payment ID -> 404 Not Found
    res_ec33 = client.get("/api/payments/id/99999", headers=auth_admin)
    print(f">> 2.1 Non-Existent Payment (EC-33): HTTP {res_ec33.status_code} (Not Found)")
    assert res_ec33.status_code == 404
    assert "payment record not found" in res_ec33.json()["detail"].lower()

    # 2.2 Valid lookup -> 200 OK
    res_by_id = client.get(f"/api/payments/id/{payment_id1}", headers=auth_admin)
    print(f">> 2.2 Valid Payment Lookup by ID: HTTP {res_by_id.status_code}")
    assert res_by_id.status_code == 200
    assert res_by_id.json()["payment_id"] == payment_id1

    # -------------------------------------------------------------------------
    # TEST SET 3: PUT /api/payments/{payment_id} - Settlement & Edge Cases
    # -------------------------------------------------------------------------
    print("\n[TEST SET 3] PUT /api/payments/{payment_id} - Updates & Settlement")
    print("-" * 75)

    # 3.1 Customer attempting to update payment status -> 403 Forbidden
    res_c_update = client.put(
        f"/api/payments/{payment_id1}",
        json={"payment_status": "Paid", "payment_method": "UPI"},
        headers=auth_cust1
    )
    print(f">> 3.1 Customer Updating Payment: HTTP {res_c_update.status_code} (Forbidden)")
    assert res_c_update.status_code == 403

    # 3.2 EC-33: Updating non-existent payment ID -> 404 Not Found
    res_upd_ec33 = client.put(
        "/api/payments/99999",
        json={"payment_status": "Paid"},
        headers=auth_admin
    )
    print(f">> 3.2 Update Non-Existent Payment (EC-33): HTTP {res_upd_ec33.status_code} (Not Found)")
    assert res_upd_ec33.status_code == 404

    # 3.3 EC-31: Zero or negative amount -> 422 Unprocessable Entity
    res_ec31 = client.put(
        f"/api/payments/{payment_id1}",
        json={"payment_status": "Paid", "amount": 0},
        headers=auth_admin
    )
    print(f">> 3.3 Zero Amount (EC-31): HTTP {res_ec31.status_code} (Rejected)")
    assert res_ec31.status_code in (400, 422)

    res_ec31_neg = client.put(
        f"/api/payments/{payment_id1}",
        json={"payment_status": "Paid", "amount": -50.0},
        headers=auth_admin
    )
    print(f">> 3.3 Negative Amount (EC-31): HTTP {res_ec31_neg.status_code} (Rejected)")
    assert res_ec31_neg.status_code in (400, 422)

    # 3.4 Valid payment settlement to 'Paid'
    settle_payload = {
        "payment_status": "Paid",
        "payment_method": "UPI",
        "amount": charge1
    }
    res_settle = client.put(f"/api/payments/{payment_id1}", json=settle_payload, headers=auth_admin)
    print(f">> 3.4 Settle Payment to 'Paid': HTTP {res_settle.status_code}")
    assert res_settle.status_code == 200
    settled_data = res_settle.json()
    assert settled_data["payment_status"] == "Paid"
    assert settled_data["payment_method"] == "Upi"
    assert settled_data["paid_at"] is not None
    print(f"    Settled at: {settled_data['paid_at']} | Method: {settled_data['payment_method']}")

    # 3.5 EC-30: Attempting to record/update payment for an already 'Paid' parcel
    res_ec30 = client.put(
        f"/api/payments/{payment_id1}",
        json={"payment_status": "Paid", "payment_method": "Cash"},
        headers=auth_admin
    )
    print(f">> 3.5 Already Paid Parcel (EC-30): HTTP {res_ec30.status_code} (Rejected: {res_ec30.json()['detail']})")
    assert res_ec30.status_code == 400
    assert "already completed" in res_ec30.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # TEST SET 4: GET /api/payments - Listing & Filtering
    # -------------------------------------------------------------------------
    print("\n[TEST SET 4] GET /api/payments - Admin Overview & Filtering")
    print("-" * 75)

    res_all_pay = client.get("/api/payments", headers=auth_admin)
    assert res_all_pay.status_code == 200
    all_payments = res_all_pay.json()
    print(f">> Total payments in system: {len(all_payments)}")

    res_paid = client.get("/api/payments?status=Paid", headers=auth_admin)
    assert res_paid.status_code == 200
    paid_list = res_paid.json()
    print(f">> Payments with status='Paid': {len(paid_list)}")
    assert all(p["payment_status"] == "Paid" for p in paid_list)

    # -------------------------------------------------------------------------
    # TEST SET 5: MongoDB Payment Settlement Event Verification
    # -------------------------------------------------------------------------
    print("\n[TEST SET 5] MongoDB Payment Event Verification")
    print("-" * 75)

    history = get_tracking_history(tid1)
    assert history is not None
    print(f">> Tracking timeline for {tid1} contains {len(history)} events:")
    for ev in history:
        print(f"    * [{ev['status']}] at {ev['location']} | Notes: {ev['notes']}")
    payment_events = [ev for ev in history if "payment" in ev["notes"].lower()]
    assert len(payment_events) >= 1, "Expected payment settlement event in MongoDB history"
    print(">> Payment settlement event successfully recorded in MongoDB!")

    print("\n" + "=" * 75)
    print("  ALL PAYMENT MANAGEMENT & EDGE CASE TESTS PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
