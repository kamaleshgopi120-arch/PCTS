"""
backend/test_auth.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 10
Automated Test Suite for Authentication, JWT, and Role-Based Access Control
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
from backend.security import hash_password, verify_password, create_access_token, decode_access_token

client = TestClient(app)


def setup_test_users():
    """Ensure our standard admin user has a valid bcrypt password hash in MySQL."""
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@pcts.com"))
        if admin:
            admin.password_hash = hash_password("Admin@12345")
            db.commit()
    finally:
        db.close()


def test_unit_security():
    print("\n[TEST SET 1] Unit Tests: Password Hashing & JWT Utilities")
    print("-" * 75)

    raw_pw = "SuperSecurePass123"
    hashed = hash_password(raw_pw)
    print(f">> Hashed Password: {hashed[:30]}...")

    # Verification
    assert verify_password(raw_pw, hashed) is True, "Password verification failed for correct password"
    assert verify_password("WrongPassword!", hashed) is False, "Password verification succeeded for wrong password"
    print(">> bcrypt password hashing and verification passed!")

    # Token creation and decode
    payload = {"sub": "test@pcts.com", "user_id": 99, "role": "customer"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "test@pcts.com"
    assert decoded["user_id"] == 99
    assert decoded["role"] == "customer"
    print(">> JWT token encoding and decoding passed!")


def test_registration_and_login():
    print("\n[TEST SET 2] Integration Tests: User Registration & Login Endpoints")
    print("-" * 75)

    test_email = "new_student_user@pondiuni.ac.in"
    test_password = "CollegeStudent2026!"

    # Clean up test user if already exists from a previous run
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == test_email))
        if existing:
            db.delete(existing)
            db.commit()
    finally:
        db.close()

    # 1. Register new customer
    reg_payload = {
        "email": test_email,
        "password": test_password,
        "role": "customer",
        "full_name": "Ramesh Sundaram",
        "phone": "9876500001",
        "address": "100, University Road, Kalapet",
        "city": "Puducherry"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    print(f">> 2.1 Register New User: HTTP {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    user_data = res.json()
    assert user_data["email"] == test_email
    assert user_data["role"] == "customer"
    print(f"   Registered user_id: {user_data['user_id']}")

    # 2. Attempt duplicate registration (EC-05)
    res_dup = client.post("/api/auth/register", json=reg_payload)
    print(f">> 2.2 Duplicate Email Registration (EC-05): HTTP {res_dup.status_code}")
    assert res_dup.status_code == 400, f"Expected 400, got {res_dup.status_code}"
    assert "already registered" in res_dup.json()["detail"]
    print("   Successfully rejected with: 'This email is already registered.'")

    # 3. Login with wrong password (EC-01)
    bad_login = {
        "email": test_email,
        "password": "WrongPassword999!"
    }
    res_bad_pw = client.post("/api/auth/login", json=bad_login)
    print(f">> 2.3 Login with Wrong Password (EC-01): HTTP {res_bad_pw.status_code}")
    assert res_bad_pw.status_code == 401, f"Expected 401, got {res_bad_pw.status_code}"
    assert res_bad_pw.json()["detail"] == "Invalid email or password."
    print("   Successfully rejected with generic: 'Invalid email or password.'")

    # 4. Login with non-existent email (EC-02)
    bad_email = {
        "email": "nonexistent_email_404@nowhere.com",
        "password": "AnyPassword123!"
    }
    res_bad_email = client.post("/api/auth/login", json=bad_email)
    print(f">> 2.4 Login with Non-Existent Email (EC-02): HTTP {res_bad_email.status_code}")
    assert res_bad_email.status_code == 401, f"Expected 401, got {res_bad_email.status_code}"
    assert res_bad_email.json()["detail"] == "Invalid email or password."
    print("   Successfully rejected with generic: 'Invalid email or password.'")

    # 5. Successful Login
    valid_login = {
        "email": test_email,
        "password": test_password
    }
    res_login = client.post("/api/auth/login", json=valid_login)
    print(f">> 2.5 Valid Login: HTTP {res_login.status_code}")
    assert res_login.status_code == 200, f"Expected 200, got {res_login.status_code}"
    token_data = res_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    customer_token = token_data["access_token"]
    print(f"   Received Bearer Token: {customer_token[:35]}...")

    return customer_token


def test_protected_routes_and_rbac(customer_token: str):
    print("\n[TEST SET 3] Protected Routes & Role-Based Access Control (RBAC)")
    print("-" * 75)

    # 1. Access /api/auth/me without token (EC-07)
    res_no_auth = client.get("/api/auth/me")
    print(f">> 3.1 Access /api/auth/me without Token (EC-07): HTTP {res_no_auth.status_code}")
    assert res_no_auth.status_code == 401, f"Expected 401, got {res_no_auth.status_code}"

    # 2. Access /api/auth/me with valid Customer Bearer Token
    headers = {"Authorization": f"Bearer {customer_token}"}
    res_me = client.get("/api/auth/me", headers=headers)
    print(f">> 3.2 Access /api/auth/me with Bearer Token: HTTP {res_me.status_code}")
    assert res_me.status_code == 200, f"Expected 200, got {res_me.status_code}"
    me_data = res_me.json()
    print(f"   User Profile: {me_data['full_name']} | Role: {me_data['role']} | City: {me_data['city']}")
    assert me_data["full_name"] == "Ramesh Sundaram"
    assert me_data["city"] == "Puducherry"

    # 3. Access Admin-only route as Customer (EC-04)
    res_admin_as_cust = client.get("/api/auth/admin-only", headers=headers)
    print(f">> 3.3 Customer Accessing Admin Endpoint (EC-04): HTTP {res_admin_as_cust.status_code}")
    assert res_admin_as_cust.status_code == 403, f"Expected 403 Forbidden, got {res_admin_as_cust.status_code}"
    print(f"   Rejected with: {res_admin_as_cust.json()['detail']}")

    # 4. Login as Admin and Access Admin-only route
    res_admin_login = client.post("/api/auth/login", json={"email": "admin@pcts.com", "password": "Admin@12345"})
    assert res_admin_login.status_code == 200, f"Admin login failed: {res_admin_login.text}"
    admin_token = res_admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    res_admin_dashboard = client.get("/api/auth/admin-only", headers=admin_headers)
    print(f">> 3.4 Admin Accessing Admin Endpoint: HTTP {res_admin_dashboard.status_code}")
    assert res_admin_dashboard.status_code == 200, f"Expected 200, got {res_admin_dashboard.status_code}"
    dash_data = res_admin_dashboard.json()
    print(f"   Dashboard Response: {dash_data['message']} | Users: {dash_data['total_registered_users']}")


if __name__ == "__main__":
    print("=" * 75)
    print("  PHASE 10: USER AUTHENTICATION & RBAC AUTOMATED TEST SUITE")
    print("=" * 75)
    setup_test_users()
    test_unit_security()
    cust_token = test_registration_and_login()
    test_protected_routes_and_rbac(cust_token)
    print("\n" + "=" * 75)
    print("  ALL AUTHENTICATION, JWT, AND RBAC TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)
