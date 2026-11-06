"""
backend/test_e2e_integration.py
=============================================================================
Parcel and Courier Tracking System (PCTS) — Phase 22: Comprehensive E2E Test
Complete Lifecycle End-to-End Integration Verification
=============================================================================
"""

import os
import sys
import uuid
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.database import SessionLocal
from backend.models.user import User
from backend.security import hash_password
from sqlalchemy import select

client = TestClient(app)


def ensure_system_users():
    """Ensure baseline admin and delivery agent accounts exist with known credentials."""
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@pcts.com"))
        if admin:
            admin.password_hash = hash_password("Admin@12345")

        deliv = db.scalar(select(User).where(User.email == "ravi.delivery@pcts.com"))
        if deliv:
            deliv.password_hash = hash_password("Delivery@12345")

        db.commit()
    finally:
        db.close()


def run_full_lifecycle_test():
    print("=" * 75)
    print("  PCTS FULL LIFECYCLE END-TO-END INTEGRATION TEST")
    print("=" * 75)

    ensure_system_users()

    uid = uuid.uuid4().hex[:6]
    cust_email = f"e2e_cust_{uid}@example.com"
    cust_pass = "SecurePass123!"

    # -------------------------------------------------------------------------
    # STAGE 1: Customer Registration & Auth
    # -------------------------------------------------------------------------
    print("\n[STAGE 1] Customer Registration & Authentication")
    reg_resp = client.post("/api/auth/register", json={
        "full_name": f"E2E Customer {uid}",
        "email": cust_email,
        "password": cust_pass,
        "phone": "9820011223",
        "city": "Mumbai",
        "address": "701, Oberoi Splendor, JVLR",
        "role": "customer"
    })
    assert reg_resp.status_code == 201, f"Customer registration failed: {reg_resp.text}"
    print(f"  [PASS] Registered customer account: {cust_email}")

    login_resp = client.post("/api/auth/login", json={
        "email": cust_email,
        "password": cust_pass
    })
    assert login_resp.status_code == 200, f"Customer login failed: {login_resp.text}"
    cust_token = login_resp.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    print("  [PASS] Customer authenticated and acquired JWT access token")

    # -------------------------------------------------------------------------
    # STAGE 2: Parcel Booking & Live Charge Calculation
    # -------------------------------------------------------------------------
    print("\n[STAGE 2] Parcel Booking & Tiered Rate Calculation")
    weight = 7.5  # Tier 3 (5.0 - 20.0 kg): 7.5 * 20 = 150.00
    book_resp = client.post("/api/parcels", headers=cust_headers, json={
        "sender_name": f"E2E Customer {uid}",
        "sender_phone": "9820011223",
        "receiver_name": "Meera Patel",
        "receiver_phone": "9833445566",
        "receiver_address": "701, Koramangala Main Road",
        "source_city": "Mumbai",
        "destination_city": "Bengaluru",
        "parcel_type": "Fragile",
        "weight_kg": weight,
        "description": "Ceramic Handicrafts & Glassware"
    })
    assert book_resp.status_code == 201, f"Booking failed: {book_resp.text}"
    parcel = book_resp.json()
    tracking_id = parcel["tracking_id"]
    parcel_id = parcel["parcel_id"]
    expected_charge = 150.0  # 7.5 * 20
    assert parcel["charge"] == expected_charge, f"Expected {expected_charge}, got {parcel['charge']}"
    assert parcel["status"] == "Booked"
    assert parcel["receiver_address"] == "701, Koramangala Main Road"
    print(f"  [PASS] Parcel booked: {tracking_id} (ID: {parcel_id})")
    print(f"         Weight: {weight} kg -> Verified Charge: Rs.{parcel['charge']}")

    # -------------------------------------------------------------------------
    # STAGE 3: Initial Public Tracking Verification
    # -------------------------------------------------------------------------
    print("\n[STAGE 3] Public Tracking (Initial State)")
    track_init = client.get(f"/api/track/{tracking_id}").json()
    assert track_init["status"] == "Booked"
    init_history = track_init.get("history") or track_init.get("events") or []
    assert len(init_history) >= 1
    print(f"  [PASS] Public Tracking confirmed initial status: '{track_init['status']}'")
    print(f"         Initial MongoDB audit event recorded at: {init_history[0]['location']}")

    # -------------------------------------------------------------------------
    # STAGE 4: Admin Operations & Delivery Assignment
    # -------------------------------------------------------------------------
    print("\n[STAGE 4] Admin Operations & Courier Assignment")
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@pcts.com",
        "password": "Admin@12345"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    deliv_login = client.post("/api/auth/login", json={
        "email": "ravi.delivery@pcts.com",
        "password": "Delivery@12345"
    })
    assert deliv_login.status_code == 200
    deliv_token = deliv_login.json()["access_token"]
    deliv_headers = {"Authorization": f"Bearer {deliv_token}"}

    # Assign the parcel to the agent who will perform the delivery.
    agents = client.get("/api/deliveries/agents", headers=admin_headers).json()
    assigned_agent = next(
        (agent for agent in agents if agent["user_id"] == deliv_login.json()["user_id"]),
        None
    )
    assert assigned_agent is not None
    agent_id = assigned_agent["delivery_person_id"]

    assign_resp = client.post("/api/deliveries", headers=admin_headers, json={
        "parcel_id": parcel_id,
        "delivery_person_id": agent_id,
        "notes": "Fragile handle with care. Electronic signature on receipt."
    })
    assert assign_resp.status_code == 201, f"Assignment failed: {assign_resp.text}"
    delivery = assign_resp.json()
    delivery_id = delivery["delivery_id"]
    print(f"  [PASS] Admin assigned parcel to Agent #{agent_id} ({assigned_agent['full_name']})")
    print(f"         Delivery Assignment ID: {delivery_id}")

    # -------------------------------------------------------------------------
    # STAGE 5: Delivery Agent Milestone Status Transitions
    # -------------------------------------------------------------------------
    print("\n[STAGE 5] Delivery Agent Milestone Progression")
    deliv_login = client.post("/api/auth/login", json={
        "email": "ravi.delivery@pcts.com",
        "password": "Delivery@12345"
    })
    assert deliv_login.status_code == 200
    deliv_token = deliv_login.json()["access_token"]
    deliv_headers = {"Authorization": f"Bearer {deliv_token}"}

    # 5.1 Status: Picked Up
    r1 = client.put(f"/api/deliveries/{delivery_id}/status", headers=deliv_headers, json={
        "status": "Picked Up",
        "location": "Bandra West Collection Point, Mumbai",
        "notes": "Collected from sender. Fragile label applied."
    })
    assert r1.status_code == 200
    print("  [PASS] Milestone 1: 'Picked Up' at Bandra West Collection Point")

    # 5.2 Status: In Transit
    r2 = client.put(f"/api/deliveries/{delivery_id}/status", headers=deliv_headers, json={
        "status": "In Transit",
        "location": "Mumbai Central Logistics Hub",
        "notes": "Dispatched via southern inter-city express corridor."
    })
    assert r2.status_code == 200
    print("  [PASS] Milestone 2: 'In Transit' at Mumbai Central Logistics Hub")

    # 5.3 Status: At Warehouse
    r3 = client.put(f"/api/deliveries/{delivery_id}/status", headers=deliv_headers, json={
        "status": "At Warehouse",
        "location": "Bengaluru Electronic City Warehouse",
        "notes": "Arrived at destination facility."
    })
    assert r3.status_code == 200
    print("  [PASS] Milestone 3: 'At Warehouse' at Bengaluru Electronic City")

    # 5.4 Status: Out for Delivery
    r4 = client.put(f"/api/deliveries/{delivery_id}/status", headers=deliv_headers, json={
        "status": "Out for Delivery",
        "location": "Bengaluru Electronic City Delivery Branch",
        "notes": "Loaded for final doorstep delivery run."
    })
    assert r4.status_code == 200
    print("  [PASS] Milestone 4: 'Out for Delivery' at Bengaluru Electronic City")

    # 5.5 Status: Delivered (Terminal State)
    r5 = client.put(f"/api/deliveries/{delivery_id}/status", headers=deliv_headers, json={
        "status": "Delivered",
        "location": "Customer Doorstep, Koramangala, Bengaluru",
        "notes": "Delivered successfully. Signed by recipient Meera Patel."
    })
    assert r5.status_code == 200
    print("  [PASS] Milestone 5: 'Delivered' at Customer Doorstep, Koramangala")

    # -------------------------------------------------------------------------
    # STAGE 6: Payment Settlement
    # -------------------------------------------------------------------------
    print("\n[STAGE 6] Payment Verification & Settle Outstanding Balance")
    pay_get = client.get(f"/api/payments/{parcel_id}", headers=cust_headers).json()
    assert pay_get["amount"] == expected_charge
    payment_id = pay_get["payment_id"]

    # Settle payment as Paid
    pay_update = client.put(f"/api/payments/{payment_id}", headers=admin_headers, json={
        "payment_status": "Paid",
        "payment_method": "UPI",
        "amount": expected_charge
    })
    assert pay_update.status_code == 200
    assert pay_update.json()["payment_status"] == "Paid"
    print(f"  [PASS] Payment ID #{payment_id} settled as 'Paid' via UPI for Rs.{expected_charge}")

    # -------------------------------------------------------------------------
    # STAGE 7: Final Comprehensive Public Tracking Verification
    # -------------------------------------------------------------------------
    print("\n[STAGE 7] Complete Chronological Audit Trail Verification")
    final_track = client.get(f"/api/track/{tracking_id}").json()
    assert final_track["status"] == "Delivered"
    assert final_track["is_delivered"] is True

    history = final_track.get("history") or final_track.get("events") or []
    # Should have at least: Booked, Picked Up, In Transit, At Warehouse, Out for Delivery, Delivered
    assert len(history) >= 6, f"Expected >= 6 milestones, found {len(history)}"

    print(f"  [PASS] Final Status: {final_track['status']} (is_delivered: {final_track['is_delivered']})")
    print(f"  [PASS] Total MongoDB audit events recorded: {len(history)}")
    for idx, ev in enumerate(history, 1):
        print(f"         {idx}. [{ev['status'].ljust(17)}] {ev['location']}")

    # -------------------------------------------------------------------------
    # STAGE 8: Admin Reports Reflection
    # -------------------------------------------------------------------------
    print("\n[STAGE 8] Administrative Analytics & Metrics Verification")
    rep_parcels = client.get("/api/reports/parcels", headers=admin_headers).json()
    assert rep_parcels["total_parcels"] > 0
    rep_payments = client.get("/api/reports/payments", headers=admin_headers).json()
    assert rep_payments["collected_amount"] > 0
    print(f"  [PASS] Analytics updated: Total Shipments: {rep_parcels['total_parcels']} | Collected Revenue: Rs.{rep_payments['collected_amount']}")

    print("\n" + "=" * 75)
    print("  FULL LIFECYCLE END-TO-END TEST PASSED WITH 100% SUCCESS! [OK]")
    print("=" * 75)


if __name__ == "__main__":
    run_full_lifecycle_test()
