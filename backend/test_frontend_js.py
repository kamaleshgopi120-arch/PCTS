"""
backend/test_frontend_js.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 20 Verification
Automated Test Suite for Frontend JavaScript Integration and API Workflows
=============================================================================
"""

import os
import sys
import re
from html.parser import HTMLParser
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.database import SessionLocal
from backend.models.user import User
from backend.security import hash_password
from sqlalchemy import select

client = TestClient(app)

def ensure_test_users():
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

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
JS_DIR = os.path.join(FRONTEND_DIR, "js")

REQUIRED_SCRIPTS = [
    "api.js",
    "auth.js",
    "book_parcel.js",
    "track.js",
    "dashboard.js",
    "delivery.js"
]

PAGE_SCRIPT_MAPPING = {
    "index.html": ["js/api.js"],
    "login.html": ["js/api.js", "js/auth.js"],
    "register.html": ["js/api.js", "js/auth.js"],
    "book_parcel.html": ["js/api.js", "js/book_parcel.js"],
    "track.html": ["js/api.js", "js/track.js"],
    "dashboard.html": ["js/api.js", "js/dashboard.js"],
    "delivery_dashboard.html": ["js/api.js", "js/delivery.js"]
}


class ScriptTagFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.script_sources = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attr_dict = dict(attrs)
            if "src" in attr_dict:
                self.script_sources.append(attr_dict["src"])


def test_javascript_files_and_html_linking():
    print("=" * 70)
    print("  PHASE 20: JAVASCRIPT FILES & HTML LINKING VERIFICATION")
    print("=" * 70)

    # 1. Verify all JS files exist and are non-empty
    for script_name in REQUIRED_SCRIPTS:
        script_path = os.path.join(JS_DIR, script_name)
        assert os.path.isfile(script_path), f"Missing JS file: {script_path}"
        size = os.path.getsize(script_path)
        assert size > 200, f"JS file too small or empty: {script_name} ({size} bytes)"
        print(f"[PASS] Found JS module: {script_name.ljust(18)} ({size} bytes)")

    # 2. Verify each HTML page links its required script files
    print("\n" + "-" * 70)
    print("  VERIFYING HTML SCRIPT TAG INCLUSIONS")
    print("-" * 70)

    for page_name, expected_scripts in PAGE_SCRIPT_MAPPING.items():
        page_path = os.path.join(FRONTEND_DIR, page_name)
        with open(page_path, "r", encoding="utf-8") as f:
            content = f.read()

        finder = ScriptTagFinder()
        finder.feed(content)

        for expected in expected_scripts:
            assert expected in finder.script_sources, (
                f"Page {page_name} missing script tag for '{expected}'. Found: {finder.script_sources}"
            )

        print(f"[PASS] {page_name.ljust(25)} -> Correctly linked: {', '.join(finder.script_sources)}")


def test_fastapi_serving_js():
    print("\n" + "=" * 70)
    print("  PHASE 20: FASTAPI STATIC SERVING OF JS ASSETS")
    print("=" * 70)

    for script_name in REQUIRED_SCRIPTS:
        resp = client.get(f"/static/js/{script_name}")
        assert resp.status_code == 200, f"Failed GET /static/js/{script_name}: {resp.status_code}"
        ct = resp.headers.get("content-type", "")
        assert "javascript" in ct or "text/plain" in ct, f"Unexpected Content-Type: {ct}"
        print(f"[PASS] GET /static/js/{script_name.ljust(18)} -> 200 OK (Content-Type: {ct})")


def test_complete_api_workflow_for_frontend():
    print("\n" + "=" * 70)
    print("  PHASE 20: COMPLETE FRONTEND END-TO-END WORKFLOW TEST")
    print("=" * 70)

    ensure_test_users()

    import uuid
    uid = uuid.uuid4().hex[:6]
    cust_email = f"js_user_{uid}@example.com"
    cust_password = "Password123!"

    # 1. Customer Registration (simulates frontend/js/auth.js: initRegisterPage)
    print("\n[Step 1] Customer Registration:")
    reg_resp = client.post("/api/auth/register", json={
        "full_name": f"JS Customer {uid}",
        "email": cust_email,
        "password": cust_password,
        "phone": "9876543210",
        "city": "Mumbai",
        "address": "404 Marine Drive, Nariman Point",
        "role": "customer"
    })
    assert reg_resp.status_code == 201, f"Reg failed: {reg_resp.text}"
    print(f"  [PASS] Registered customer: {cust_email} (HTTP 201)")

    # 2. Customer Login (simulates frontend/js/auth.js: initLoginPage)
    print("\n[Step 2] Customer Login:")
    login_resp = client.post("/api/auth/login", json={
        "email": cust_email,
        "password": cust_password
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token_data = login_resp.json()
    token = token_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print(f"  [PASS] Received JWT Token: {token[:16]}... (HTTP 200)")

    # 3. Customer Profile Check (simulates api.js: initNavbarAuth)
    print("\n[Step 3] Profile Retrieval (GET /api/auth/me):")
    me_resp = client.get("/api/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["role"] == "customer"
    assert me_data["full_name"] == f"JS Customer {uid}"
    print(f"  [PASS] Profile loaded: {me_data['full_name']} | Role: {me_data['role']}")

    # 4. Parcel Booking (simulates frontend/js/book_parcel.js: submit)
    print("\n[Step 4] Parcel Booking (POST /api/parcels):")
    book_resp = client.post("/api/parcels", headers=auth_headers, json={
        "sender_name": f"JS Customer {uid}",
        "sender_phone": "9876543210",
        "receiver_name": "Rohan Recipient",
        "receiver_phone": "9811223344",
        "source_city": "Mumbai",
        "destination_city": "Delhi",
        "parcel_type": "Electronics",
        "weight_kg": 3.5,
        "description": "Smart Watch and Wireless Earbuds"
    })
    assert book_resp.status_code == 201, f"Booking failed: {book_resp.text}"
    parcel_data = book_resp.json()
    tracking_id = parcel_data["tracking_id"]
    parcel_id = parcel_data["parcel_id"]
    # 3.5kg falls in tier 2 (1-5kg): 3.5 * 30 = 105.00
    assert parcel_data["charge"] == 105.0
    print(f"  [PASS] Booked parcel with ID: {parcel_id} | Tracking ID: {tracking_id} | Charge: Rs.{parcel_data['charge']}")

    # 5. Public Parcel Tracking (simulates frontend/js/track.js)
    print("\n[Step 5] Public Tracking (GET /api/track/{tracking_id}):")
    track_resp = client.get(f"/api/track/{tracking_id}")
    assert track_resp.status_code == 200, f"Tracking failed: {track_resp.text}"
    track_data = track_resp.json()
    assert track_data["status"] == "Booked"
    history = track_data.get("history") or track_data.get("events") or []
    assert len(history) >= 1
    print(f"  [PASS] Current Status: {track_data['status']} | Events logged: {len(history)}")

    # 6. Admin Login & Agent Assignment (simulates frontend/js/dashboard.js)
    print("\n[Step 6] Admin Assigns Parcel (POST /api/deliveries):")
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@pcts.com",
        "password": "Admin@12345"
    })
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Fetch available agents
    agents_resp = client.get("/api/deliveries/agents", headers=admin_headers)
    assert agents_resp.status_code == 200
    agents = agents_resp.json()
    assert len(agents) > 0
    assigned_agent = agents[0]
    agent_id = assigned_agent["delivery_person_id"]

    # Assign parcel
    assign_resp = client.post("/api/deliveries", headers=admin_headers, json={
        "parcel_id": parcel_id,
        "delivery_person_id": agent_id,
        "notes": "Express delivery assignment via dashboard"
    })
    assert assign_resp.status_code == 201, f"Assignment failed: {assign_resp.text}"
    delivery_info = assign_resp.json()
    delivery_id = delivery_info["delivery_id"]
    print(f"  [PASS] Parcel {tracking_id} assigned to Agent #{agent_id} ({assigned_agent['full_name']}) | Delivery ID: {delivery_id}")

    # 7. Delivery Agent Login & Task View (simulates frontend/js/delivery.js)
    print("\n[Step 7] Delivery Agent Workflow (GET /api/deliveries/my & PUT status):")
    agent_login = client.post("/api/auth/login", json={
        "email": "ravi.delivery@pcts.com",
        "password": "Delivery@12345"
    })
    assert agent_login.status_code == 200, f"Agent login failed: {agent_login.text}"
    agent_token = agent_login.json()["access_token"]
    agent_headers = {"Authorization": f"Bearer {agent_token}"}

    # Agent checks queue
    my_tasks = client.get("/api/deliveries/my", headers=agent_headers).json()
    matching = [t for t in my_tasks if t["delivery_id"] == delivery_id]
    assert len(matching) == 1
    print(f"  [PASS] Agent task queue contains assigned parcel: {tracking_id} (Status: {matching[0]['status']})")

    # Agent updates milestone to "In Transit"
    status_resp = client.put(f"/api/deliveries/{delivery_id}/status", headers=agent_headers, json={
        "status": "In Transit",
        "location": "Mumbai Central Freight Terminal",
        "notes": "Loaded into express container truck MH-01-AB-1234"
    })
    assert status_resp.status_code == 200, f"Status update failed: {status_resp.text}"
    print(f"  [PASS] Agent updated milestone -> Status: In Transit at 'Mumbai Central Freight Terminal'")

    # 8. Verify Updated Tracking View (simulates frontend/js/track.js with updated MongoDB timeline)
    print("\n[Step 8] Live Tracking Refreshed Timeline Check:")
    track_updated = client.get(f"/api/track/{tracking_id}").json()
    assert track_updated["status"] == "In Transit"
    updated_history = track_updated.get("history") or track_updated.get("events") or []
    assert len(updated_history) >= 2
    latest_event = updated_history[-1]
    assert latest_event["status"] == "In Transit"
    assert "Mumbai Central" in latest_event["location"]
    print(f"  [PASS] Live Tracking updated! Current Status: {track_updated['status']}")
    print(f"         Latest Event: {latest_event['status']} at {latest_event['location']}")

    print("\n" + "=" * 70)
    print("  ALL PHASE 20 JAVASCRIPT INTEGRATION WORKFLOW TESTS PASSED! [OK]")
    print("=" * 70)


if __name__ == "__main__":
    test_javascript_files_and_html_linking()
    test_fastapi_serving_js()
    test_complete_api_workflow_for_frontend()
