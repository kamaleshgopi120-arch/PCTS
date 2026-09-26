"""
backend/test_tracking.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 13
Automated Test Suite for Public Tracking, Status Updates & Trigger Verification
=============================================================================
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
from backend.security import create_access_token

client = TestClient(app)


def get_tokens():
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@pcts.com"))
        admin_tok = create_access_token({"sub": admin.email, "user_id": admin.user_id, "role": "admin"})

        cust = db.scalar(select(User).where(User.email == "arun.kumar@gmail.com"))
        cust_tok = create_access_token({"sub": cust.email, "user_id": cust.user_id, "role": "customer"})

        deliv = db.scalar(select(User).where(User.email == "ravi.delivery@pcts.com"))
        deliv_tok = create_access_token({"sub": deliv.email, "user_id": deliv.user_id, "role": "delivery"})

        return admin_tok, cust_tok, deliv_tok
    finally:
        db.close()


def test_public_tracking():
    print("\n[TEST SET 1] GET /api/track/{id} - Public Tracking Endpoint")
    print("-" * 75)

    valid_tracking_id = "PCTS-20240925-0001"

    # 1.1 Track with valid Tracking ID (No auth header needed)
    res = client.get(f"/api/track/{valid_tracking_id}")
    print(f">> 1.1 Public Tracking (No Auth): HTTP {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    print(f"   Tracking ID:  {data['tracking_id']}")
    print(f"   Route:        {data['source_city']} -> {data['destination_city']}")
    print(f"   Status:       {data['status']} ({data['location']})")
    assert data["tracking_id"] == valid_tracking_id
    assert "source_city" in data

    # 1.2 Track with spaces and lowercase (EC-20: Auto-normalization)
    messy_id = f"   {valid_tracking_id.lower()}   "
    res_norm = client.get(f"/api/track/{messy_id}")
    print(f">> 1.2 Whitespace & Lowercase Input (EC-20): HTTP {res_norm.status_code} (Normalized)")
    assert res_norm.status_code == 200
    assert res_norm.json()["tracking_id"] == valid_tracking_id

    # 1.3 Non-existent Tracking ID (EC-19)
    res_fake = client.get("/api/track/PCTS-NONEXISTENT-9999")
    print(f">> 1.3 Non-Existent Tracking ID (EC-19): HTTP {res_fake.status_code} (Not Found)")
    assert res_fake.status_code == 404
    assert res_fake.json()["detail"] == "No parcel found with this Tracking ID."


def test_status_update_and_trigger(admin_token, cust_token, deliv_token):
    print("\n[TEST SET 2] PUT /api/parcels/{id}/status - Status Updates & Trigger Audit")
    print("-" * 75)

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    deliv_headers = {"Authorization": f"Bearer {deliv_token}"}

    # 2.1 Unauthenticated attempt
    res_no_auth = client.put("/api/parcels/1/status", json={"status": "In Transit", "location": "Hub"})
    print(f">> 2.1 Without Token: HTTP {res_no_auth.status_code}")
    assert res_no_auth.status_code == 401

    # 2.2 Customer attempt (Forbidden - requires Staff/Admin)
    res_cust = client.put("/api/parcels/1/status", json={"status": "In Transit", "location": "Hub"}, headers=cust_headers)
    print(f">> 2.2 Customer Updating Status: HTTP {res_cust.status_code} (Forbidden)")
    assert res_cust.status_code == 403

    # 2.3 Delivery Agent updating status
    update_payload = {
        "status": "In Transit",
        "location": "Vellore Highway Sorting Facility"
    }
    res_update = client.put("/api/parcels/1/status", json=update_payload, headers=deliv_headers)
    print(f">> 2.3 Delivery Agent Updating Status: HTTP {res_update.status_code}")
    assert res_update.status_code == 200
    updated_parcel = res_update.json()
    assert updated_parcel["status"] == "In Transit"
    assert updated_parcel["location"] == "Vellore Highway Sorting Facility"
    print(f"   Updated Status: {updated_parcel['status']} at {updated_parcel['location']}")

    # 2.4 Update to 'Delivered'
    delivered_payload = {
        "status": "Delivered",
        "location": "Bengaluru Central Office"
    }
    res_deliv = client.put("/api/parcels/1/status", json=delivered_payload, headers=admin_headers)
    assert res_deliv.status_code == 200
    print(f">> 2.4 Admin Marks 'Delivered': HTTP {res_deliv.status_code}")

    # Verify public tracking reflects delivery
    res_track = client.get("/api/track/PCTS-20240925-0001")
    assert res_track.status_code == 200
    track_info = res_track.json()
    assert track_info["is_delivered"] is True
    assert track_info["status"] == "Delivered"
    print("   Public tracking successfully reflects 'Delivered' state!")

    # 2.5 VERIFY DATABASE TRIGGER `trg_after_status_update`
    print("\n[TEST SET 3] Verifying MySQL Audit Trigger Execution")
    print("-" * 75)
    db = SessionLocal()
    try:
        # Check audit rows for parcel_id 1
        query = text("""
            SELECT audit_id, parcel_id, old_status, new_status, old_location, new_location, changed_at
            FROM parcel_status_audit
            WHERE parcel_id = 1
            ORDER BY audit_id DESC
            LIMIT 2;
        """)
        rows = db.execute(query).fetchall()
        print(f">> Audit records created by trg_after_status_update trigger: {len(rows)}")
        assert len(rows) > 0, "Database trigger trg_after_status_update did not record audit row!"
        for r in rows:
            print(f"   Audit #{r.audit_id} | Status: '{r.old_status}' -> '{r.new_status}' | New Location: {r.new_location}")
        print(">> Confirmed database trigger fired and created audit log successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 75)
    print("  PHASE 13: PARCEL STATUS & TRACKING API AUTOMATED TEST SUITE")
    print("=" * 75)
    adm_tok, cu_tok, de_tok = get_tokens()
    test_public_tracking()
    test_status_update_and_trigger(adm_tok, cu_tok, de_tok)
    print("\n" + "=" * 75)
    print("  ALL TRACKING, STATUS UPDATE, AND TRIGGER TESTS PASSED!")
    print("=" * 75)
