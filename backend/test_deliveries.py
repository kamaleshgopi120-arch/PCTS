"""
backend/test_deliveries.py — Phase 15: Delivery Management API Automated Test Suite
===================================================================================
Automated verification for delivery assignment, agent queues, milestone updates,
and edge cases (EC-22, EC-23, EC-24, EC-25, EC-26, EC-27, EC-28, EC-29).
===================================================================================
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import select, text

from backend.main import app
from backend.database import SessionLocal
from backend.models.user import User
from backend.models.parcel import Parcel
from backend.models.parcel_status import ParcelStatus
from backend.models.delivery import Delivery
from backend.models.delivery_person import DeliveryPerson
from backend.security import create_access_token
from backend.mongo import get_tracking_history

client = TestClient(app)


def print_section(title: str):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def get_test_tokens():
    """Retrieve verified JWT tokens for admin, delivery agent, and customer."""
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@pcts.com"))
        admin_tok = create_access_token({"sub": admin.email, "user_id": admin.user_id, "role": "admin"})

        cust = db.scalar(select(User).where(User.email == "arun.kumar@gmail.com"))
        cust_tok = create_access_token({"sub": cust.email, "user_id": cust.user_id, "role": "customer"})

        deliv = db.scalar(select(User).where(User.email == "ravi.delivery@pcts.com"))
        deliv_tok = create_access_token({"sub": deliv.email, "user_id": deliv.user_id, "role": "delivery"})

        return admin_tok, cust_tok, deliv_tok, deliv.delivery_person.delivery_person_id
    finally:
        db.close()


def book_test_parcel(auth_headers: dict) -> tuple[int, str]:
    """Helper to book a fresh parcel for assignment tests."""
    payload = {
        "sender_name": "Test Sender",
        "sender_phone": "9876543210",
        "receiver_name": "Test Receiver",
        "receiver_phone": "9123456780",
        "source_city": "Chennai",
        "destination_city": "Coimbatore",
        "parcel_type": "General",
        "weight_kg": 3.0,
        "description": "Electronic components for testing"
    }
    res = client.post("/api/parcels", json=payload, headers=auth_headers)
    assert res.status_code == 201, f"Parcel booking failed: {res.text}"
    data = res.json()
    return data["parcel_id"], data["tracking_id"]


def run_tests():
    print_section("PHASE 15: DELIVERY MANAGEMENT API AUTOMATED TEST SUITE")

    admin_tok, cust_tok, deliv_tok, deliv_agent_id = get_test_tokens()
    auth_admin = {"Authorization": f"Bearer {admin_tok}"}
    auth_cust = {"Authorization": f"Bearer {cust_tok}"}
    auth_deliv = {"Authorization": f"Bearer {deliv_tok}"}

    # -------------------------------------------------------------------------
    # TEST SET 1: Delivery Agent Roster & Permissions
    # -------------------------------------------------------------------------
    print("\n[TEST SET 1] GET /api/deliveries/agents - Agent Roster & Access Control")
    print("-" * 75)

    # 1.1 Without token -> 401
    res1 = client.get("/api/deliveries/agents")
    print(f">> 1.1 Without Token: HTTP {res1.status_code}")
    assert res1.status_code == 401

    # 1.2 Customer accessing agent roster -> 403 Forbidden
    res2 = client.get("/api/deliveries/agents", headers=auth_cust)
    print(f">> 1.2 Customer Access: HTTP {res2.status_code} (Forbidden)")
    assert res2.status_code == 403

    # 1.3 Staff / Admin accessing agent roster -> 200 OK
    res3 = client.get("/api/deliveries/agents", headers=auth_admin)
    print(f">> 1.3 Admin Access: HTTP {res3.status_code}")
    assert res3.status_code == 200
    agents = res3.json()
    assert len(agents) >= 1
    print(f"    Total active agents found: {len(agents)} (e.g. {agents[0]['full_name']} - {agents[0]['phone']})")

    # -------------------------------------------------------------------------
    # TEST SET 2: Parcel Assignment (POST /api/deliveries) & Edge Cases
    # -------------------------------------------------------------------------
    print("\n[TEST SET 2] POST /api/deliveries - Assignment Workflow & Edge Cases")
    print("-" * 75)

    # 2.1 Customer attempting assignment -> 403 Forbidden
    res_c = client.post("/api/deliveries", json={"parcel_id": 1, "delivery_person_id": deliv_agent_id}, headers=auth_cust)
    print(f">> 2.1 Customer Assigning: HTTP {res_c.status_code} (Forbidden)")
    assert res_c.status_code == 403

    # 2.2 EC-29: Assigning non-existent parcel -> 404 Not Found
    res_ec29 = client.post("/api/deliveries", json={"parcel_id": 99999, "delivery_person_id": deliv_agent_id}, headers=auth_admin)
    print(f">> 2.2 Non-Existent Parcel (EC-29): HTTP {res_ec29.status_code} (Not Found)")
    assert res_ec29.status_code == 404

    # Book a fresh parcel for assignment tests
    pid, tid = book_test_parcel(auth_cust)
    print(f">> Created test parcel #{pid} ({tid})")

    # 2.3 EC-28: Assigning to non-existent delivery person -> 400 Bad Request
    res_ec28 = client.post("/api/deliveries", json={"parcel_id": pid, "delivery_person_id": 99999}, headers=auth_admin)
    print(f">> 2.3 Non-Existent Agent (EC-28): HTTP {res_ec28.status_code} (Rejected: {res_ec28.json()['detail']})")
    assert res_ec28.status_code == 400
    assert "delivery person not found" in res_ec28.json()["detail"].lower()

    # 2.4 Admin assigns parcel to agent -> 201 Created
    assign_payload = {"parcel_id": pid, "delivery_person_id": deliv_agent_id}
    res_assign = client.post("/api/deliveries", json=assign_payload, headers=auth_admin)
    print(f">> 2.4 Valid Assignment: HTTP {res_assign.status_code}")
    assert res_assign.status_code == 201
    assigned_data = res_assign.json()
    delivery_id = assigned_data["delivery_id"]
    assert assigned_data["status"] == "Picked Up"
    print(f"    Assignment ID: #{delivery_id} | Agent: {assigned_data['delivery_person_name']} | Status: {assigned_data['status']}")

    # 2.5 EC-26: Re-assigning the same parcel -> 400 Bad Request
    res_ec26 = client.post("/api/deliveries", json=assign_payload, headers=auth_admin)
    print(f">> 2.5 Duplicate Assignment (EC-26): HTTP {res_ec26.status_code} (Rejected: {res_ec26.json()['detail']})")
    assert res_ec26.status_code == 400
    assert "already assigned" in res_ec26.json()["detail"].lower()

    # 2.6 EC-27: Assigning an already delivered parcel -> 400 Bad Request
    # Parcel #1 in sample data is Delivered
    res_ec27 = client.post("/api/deliveries", json={"parcel_id": 1, "delivery_person_id": deliv_agent_id}, headers=auth_admin)
    print(f">> 2.6 Delivered Parcel Assignment (EC-27): HTTP {res_ec27.status_code} (Rejected: {res_ec27.json()['detail']})")
    assert res_ec27.status_code == 400
    assert "delivered" in res_ec27.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # TEST SET 3: Delivery Person Queue (GET /api/deliveries/my)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 3] GET /api/deliveries/my - Agent Work Queue")
    print("-" * 75)

    # 3.1 Customer accessing agent queue -> 403 Forbidden
    res_my_c = client.get("/api/deliveries/my", headers=auth_cust)
    print(f">> 3.1 Customer Accessing /my: HTTP {res_my_c.status_code} (Forbidden)")
    assert res_my_c.status_code == 403

    # 3.2 Delivery agent viewing assigned deliveries -> 200 OK
    res_my = client.get("/api/deliveries/my", headers=auth_deliv)
    print(f">> 3.2 Agent Viewing Own Queue: HTTP {res_my.status_code}")
    assert res_my.status_code == 200
    my_deliveries = res_my.json()
    assert len(my_deliveries) >= 1
    found_ids = [d["delivery_id"] for d in my_deliveries]
    assert delivery_id in found_ids
    print(f"    Total assigned shipments in queue: {len(my_deliveries)}")
    print(f"    Target delivery #{delivery_id} present in queue.")

    # 3.3 Filtering completed vs pending deliveries
    res_pending = client.get("/api/deliveries/my?completed=false", headers=auth_deliv)
    assert res_pending.status_code == 200
    print(f">> 3.3 Filter Pending Deliveries: Found {len(res_pending.json())} pending tasks.")

    # -------------------------------------------------------------------------
    # TEST SET 4: Status Updates & State Transitions (PUT /api/deliveries/{id}/status)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 4] PUT /api/deliveries/{id}/status - Status Transitions & Edge Cases")
    print("-" * 75)

    # 4.1 EC-22: Invalid status value
    res_ec22 = client.put(
        f"/api/deliveries/{delivery_id}/status",
        json={"status": "Flying In Space", "location": "Orbit"},
        headers=auth_deliv
    )
    print(f">> 4.1 Invalid Status Name (EC-22): HTTP {res_ec22.status_code} (Rejected)")
    assert res_ec22.status_code in (400, 422)

    # 4.2 EC-24: Invalid status transition (e.g. Picked Up -> Returned directly)
    res_ec24 = client.put(
        f"/api/deliveries/{delivery_id}/status",
        json={"status": "Returned", "location": "Hub"},
        headers=auth_deliv
    )
    print(f">> 4.2 Invalid State Transition (EC-24): HTTP {res_ec24.status_code} (Rejected: {res_ec24.json()['detail']})")
    assert res_ec24.status_code == 400
    assert "invalid status transition" in res_ec24.json()["detail"].lower()

    # 4.3 Valid transition: Picked Up -> In Transit
    res_t1 = client.put(
        f"/api/deliveries/{delivery_id}/status",
        json={"status": "In Transit", "location": "Salem Highway Checkpoint", "notes": "On express van"},
        headers=auth_deliv
    )
    print(f">> 4.3 Transition to 'In Transit': HTTP {res_t1.status_code}")
    assert res_t1.status_code == 200
    assert res_t1.json()["status"] == "In Transit"

    # 4.4 Valid transition: In Transit -> Out for Delivery
    res_t2 = client.put(
        f"/api/deliveries/{delivery_id}/status",
        json={"status": "Out for Delivery", "location": "Coimbatore Local Hub", "notes": "Loaded for doorstep delivery"},
        headers=auth_deliv
    )
    print(f">> 4.4 Transition to 'Out for Delivery': HTTP {res_t2.status_code}")
    assert res_t2.status_code == 200
    assert res_t2.json()["status"] == "Out for Delivery"

    # 4.5 Valid transition: Out for Delivery -> Delivered
    res_t3 = client.put(
        f"/api/deliveries/{delivery_id}/status",
        json={"status": "Delivered", "location": "Coimbatore Recipient Doorstep", "notes": "Delivered and verified"},
        headers=auth_deliv
    )
    print(f">> 4.5 Transition to 'Delivered': HTTP {res_t3.status_code}")
    assert res_t3.status_code == 200
    deliv_record = res_t3.json()
    assert deliv_record["status"] == "Delivered"
    assert deliv_record["delivered_at"] is not None
    print(f"    Delivered Timestamp: {deliv_record['delivered_at']}")

    # 4.6 EC-23: Cannot update status of a delivered parcel
    res_ec23 = client.put(
        f"/api/deliveries/{delivery_id}/status",
        json={"status": "In Transit", "location": "Anywhere"},
        headers=auth_deliv
    )
    print(f">> 4.6 Update Delivered Parcel (EC-23): HTTP {res_ec23.status_code} (Rejected: {res_ec23.json()['detail']})")
    assert res_ec23.status_code == 400
    assert "cannot update status of a delivered parcel" in res_ec23.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # TEST SET 5: Audit Trigger & MongoDB History Verification
    # -------------------------------------------------------------------------
    print("\n[TEST SET 5] MySQL Trigger & MongoDB Event Stream Verification")
    print("-" * 75)

    # Verify MySQL Trigger logged the status changes
    db = SessionLocal()
    try:
        audit_rows = db.execute(
            text(
                "SELECT old_status, new_status, new_location FROM parcel_status_audit "
                "WHERE parcel_id = :pid ORDER BY audit_id DESC"
            ),
            {"pid": pid}
        ).fetchall()
        print(f">> MySQL Trigger logged {len(audit_rows)} audit rows for parcel #{pid}:")
        for row in audit_rows:
            print(f"    * '{row[0]}' -> '{row[1]}' at '{row[2]}'")
        assert len(audit_rows) >= 3, "Expected at least 3 audit entries from status transitions"
    finally:
        db.close()

    # Verify MongoDB tracking history
    mongo_events = get_tracking_history(tid)
    assert mongo_events is not None
    print(f">> MongoDB logged {len(mongo_events)} chronological milestones for {tid}:")
    for ev in mongo_events:
        print(f"    -> [{ev['status']}] {ev['location']} | Notes: {ev['notes']}")
    assert len(mongo_events) >= 4, "Expected at least 4 MongoDB milestones (Booked, Picked Up, In Transit, Out for Delivery, Delivered)"

    # Verify Public Tracking returns full route
    res_pub = client.get(f"/api/track/{tid}")
    assert res_pub.status_code == 200
    pub_data = res_pub.json()
    assert pub_data["status"] == "Delivered"
    assert pub_data["is_delivered"] is True
    print(f">> Public Tracking Verified: {pub_data['tracking_id']} is Delivered ({len(pub_data['history'])} timeline milestones).")

    print("\n" + "=" * 75)
    print("  ALL DELIVERY MANAGEMENT & EDGE CASE TESTS PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
