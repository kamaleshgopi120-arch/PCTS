"""
backend/test_mongo.py — Phase 14: MongoDB Integration Automated Test Suite
=============================================================================
This test suite verifies:
1. MongoDB connection, health checks, and document storage functions.
2. Logging of tracking milestone events during parcel booking and status updates.
3. Chronological tracking history retrieval in GET /api/track/{tracking_id}.
4. Fault tolerance and resilience:
   - EC-21: When MongoDB is unavailable, tracking returns MySQL status with a warning.
   - EC-35: Parcel status updates in MySQL continue even if MongoDB logging fails.
=============================================================================
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone
import mongomock
from fastapi.testclient import TestClient

from backend.main import app
from backend.mongo import (
    log_tracking_event,
    get_tracking_history,
    set_mock_client,
    is_mongo_connected,
    COLLECTION_NAME,
    MONGO_DB_NAME,
)

from backend.database import SessionLocal
from backend.models.user import User
from backend.security import create_access_token
from sqlalchemy import select

client = TestClient(app)


def print_section(title: str):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def get_auth_tokens():
    """Retrieve verified JWT tokens for admin and customer users."""
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@pcts.com"))
        admin_tok = create_access_token({"sub": admin.email, "user_id": admin.user_id, "role": "admin"})

        cust = db.scalar(select(User).where(User.email == "arun.kumar@gmail.com"))
        cust_tok = create_access_token({"sub": cust.email, "user_id": cust.user_id, "role": "customer"})

        return admin_tok, cust_tok
    finally:
        db.close()


def run_tests():
    print_section("PHASE 14: MONGODB INTEGRATION & TRACKING HISTORY TEST SUITE")

    # Start with real live MongoDB client
    set_mock_client(None)
    live_connected = is_mongo_connected()
    print(f">> Connected to live MongoDB server: {live_connected}")
    assert live_connected is True, "Expected live MongoDB server to be running and reachable!"

    # -------------------------------------------------------------------------
    # TEST SET 1: Unit Testing backend/mongo.py Functions (Live MongoDB)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 1] Unit Tests: MongoDB Operations & Schema Validation")
    print("-" * 75)

    test_tid = f"PCTS-TEST-UNIT-{int(datetime.now().timestamp())}"

    # 1.1 Insert tracking event
    success1 = log_tracking_event(
        tracking_id=test_tid,
        status="Booked",
        location="Chennai Booking Hub",
        updated_by="staff_user",
        notes="Package weighed and accepted."
    )
    assert success1 is True, "Expected log_tracking_event to return True"
    print(">> 1.1 First tracking event logged successfully into MongoDB.")

    # 1.2 Insert second tracking event
    success2 = log_tracking_event(
        tracking_id=test_tid,
        status="In Transit",
        location="Vellore Transit Hub",
        updated_by="delivery_agent",
        notes="Dispatched on Truck TN-01-A-1234."
    )
    assert success2 is True
    print(">> 1.2 Second tracking milestone logged successfully.")

    # 1.3 Retrieve history
    history = get_tracking_history(test_tid)
    assert history is not None, "Expected tracking history to be returned"
    assert len(history) == 2, f"Expected 2 events, got {len(history)}"
    assert history[0]["status"] == "Booked"
    assert history[1]["status"] == "In Transit"
    assert history[0]["location"] == "Chennai Booking Hub"
    print(f">> 1.3 Retrieved {len(history)} chronological milestone events from MongoDB:")
    for ev in history:
        print(f"     * [{ev['status']}] at {ev['location']} (by: {ev['updated_by']}) - Notes: {ev['notes']}")

    # -------------------------------------------------------------------------
    # TEST SET 2: End-to-End API Integration (MySQL + MongoDB)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 2] Integration Tests: Parcel Booking & Status Updates")
    print("-" * 75)

    admin_token, customer_token = get_auth_tokens()
    auth_customer = {"Authorization": f"Bearer {customer_token}"}
    auth_admin = {"Authorization": f"Bearer {admin_token}"}

    # 2.1 Book a new parcel
    booking_payload = {
        "sender_name": "Kavitha Raj",
        "sender_phone": "9876543210",
        "receiver_name": "Suresh Babu",
        "receiver_phone": "9123456780",
        "receiver_address": "12 Madurai Road",
        "source_city": "Chennai",
        "destination_city": "Madurai",
        "parcel_type": "General",
        "weight_kg": 2.5,
        "description": "Textbooks and study material"
    }

    res_book = client.post("/api/parcels", json=booking_payload, headers=auth_customer)
    assert res_book.status_code == 201, f"Booking failed: {res_book.text}"
    booked_parcel = res_book.json()
    new_pid = booked_parcel["parcel_id"]
    new_tid = booked_parcel["tracking_id"]
    print(f">> 2.1 Booked new parcel #{new_pid} with Tracking ID: {new_tid}")

    # Verify initial "Booked" event was recorded in MongoDB
    history_after_book = get_tracking_history(new_tid)
    assert history_after_book is not None and len(history_after_book) >= 1
    assert history_after_book[0]["status"] == "Booked"
    print(">> Initial 'Booked' milestone automatically recorded in MongoDB!")

    # 2.2 Update status to 'In Transit' via PUT /api/parcels/{id}/status
    update_payload_1 = {
        "status": "In Transit",
        "location": "Tiruchirappalli Sorting Facility",
        "notes": "Departed regional hub on express van"
    }
    res_upd1 = client.put(f"/api/parcels/{new_pid}/status", json=update_payload_1, headers=auth_admin)
    assert res_upd1.status_code == 200, f"Status update failed: {res_upd1.text}"
    print(">> 2.2 Admin updated parcel status to 'In Transit'.")

    # 2.3 Update status to 'Delivered'
    update_payload_2 = {
        "status": "Delivered",
        "location": "Madurai West Destination Hub",
        "notes": "Handed over to receiver Suresh Babu with OTP verification"
    }
    res_upd2 = client.put(f"/api/parcels/{new_pid}/status", json=update_payload_2, headers=auth_admin)
    assert res_upd2.status_code == 200, f"Delivered update failed: {res_upd2.text}"
    print(">> 2.3 Admin marked parcel as 'Delivered'.")

    # 2.4 Query Public Tracking endpoint GET /api/track/{tracking_id}
    res_track = client.get(f"/api/track/{new_tid}")
    assert res_track.status_code == 200, f"Tracking failed: {res_track.text}"
    track_data = res_track.json()

    assert track_data["tracking_id"] == new_tid
    assert track_data["status"] == "Delivered"
    assert track_data["is_delivered"] is True
    assert track_data["warning"] is None
    assert len(track_data["history"]) == 3, f"Expected 3 milestones, got {len(track_data['history'])}"

    print(">> 2.4 Public tracking returns combined MySQL data + MongoDB history:")
    print(f"     Tracking ID: {track_data['tracking_id']}")
    print(f"     Current Status: {track_data['status']} at {track_data['location']}")
    print(f"     Timeline ({len(track_data['history'])} milestones):")
    for step in track_data["history"]:
        print(f"       -> [{step['status']}] {step['location']} ({step['timestamp'][:19]}) | {step['notes']}")

    # -------------------------------------------------------------------------
    # TEST SET 3: Fault Tolerance & Fallback Handling (EC-21 & EC-35)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 3] Resilience & Edge Cases: EC-21 & EC-35 (MongoDB Unavailable)")
    print("-" * 75)

    # 3.1 Simulate MongoDB being offline/unavailable
    class BrokenMongoClient:
        """Simulates an unreachable MongoDB instance raising connection errors."""
        def __getitem__(self, item):
            raise mongomock.filtering.ConnectionFailure("Simulated network timeout connecting to MongoDB")

    set_mock_client(BrokenMongoClient())

    # Verify public tracking gracefully degrades according to EC-21
    res_track_offline = client.get(f"/api/track/{new_tid}")
    assert res_track_offline.status_code == 200, "Tracking should succeed even if MongoDB is offline (EC-21)"
    offline_data = res_track_offline.json()

    assert offline_data["status"] == "Delivered", "Current status should still be read from MySQL"
    assert offline_data["history"] == [], "History should be empty when MongoDB is offline"
    assert offline_data["warning"] == "Tracking history is temporarily unavailable.", (
        f"Expected EC-21 warning, got: {offline_data.get('warning')}"
    )
    print(">> 3.1 EC-21 Verified:")
    print(f"     MySQL Status: {offline_data['status']}")
    print(f"     History:      {offline_data['history']}")
    print(f"     Warning:      '{offline_data['warning']}'")

    # 3.2 Verify status update still commits in MySQL even if MongoDB is down (EC-35)
    update_payload_3 = {
        "status": "In Transit",
        "location": "Emergency Route Checkpoint",
        "notes": "Rerouted due to road work"
    }
    res_upd_offline = client.put(f"/api/parcels/{new_pid}/status", json=update_payload_3, headers=auth_admin)
    assert res_upd_offline.status_code == 200, "Status update must succeed in MySQL even if MongoDB fails (EC-35)"
    print(">> 3.2 EC-35 Verified: Status update in MySQL succeeded while MongoDB was offline.")

    # Restore live MongoDB client
    set_mock_client(None)

    print("\n" + "=" * 75)
    print("  ALL MONGODB INTEGRATION, TRACKING HISTORY, AND EC-21/35 TESTS PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
