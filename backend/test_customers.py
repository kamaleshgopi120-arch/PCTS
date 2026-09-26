"""
backend/test_customers.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 11
Automated Test Suite for Customer Management CRUD API Endpoints
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
from backend.security import hash_password, create_access_token

client = TestClient(app)


def get_auth_tokens():
    """Generates valid JWT tokens for Admin and Customer test accounts."""
    db = SessionLocal()
    try:
        # 1. Admin User
        admin = db.scalar(select(User).where(User.email == "admin@pcts.com"))
        if not admin:
            admin = User(email="admin@pcts.com", password_hash=hash_password("Admin@12345"), role="admin")
            db.add(admin)
            db.commit()
            db.refresh(admin)
        admin_token = create_access_token({"sub": admin.email, "user_id": admin.user_id, "role": "admin"})

        # 2. Customer 1 (Arun Kumar)
        cust1_user = db.scalar(select(User).where(User.email == "arun.kumar@gmail.com"))
        cust1_token = create_access_token({"sub": cust1_user.email, "user_id": cust1_user.user_id, "role": "customer"})

        # 3. Customer 2 (Priya Sharma)
        cust2_user = db.scalar(select(User).where(User.email == "priya.sharma@yahoo.com"))
        cust2_token = create_access_token({"sub": cust2_user.email, "user_id": cust2_user.user_id, "role": "customer"})

        return admin_token, cust1_token, cust2_token
    finally:
        db.close()


def test_list_customers(admin_token, cust1_token):
    print("\n[TEST SET 1] GET /api/customers - Listing and Pagination")
    print("-" * 75)

    # 1.1 Unauthenticated request
    res_no_auth = client.get("/api/customers")
    print(f">> 1.1 Without Token: HTTP {res_no_auth.status_code}")
    assert res_no_auth.status_code == 401

    # 1.2 Customer accessing customer list (Requires Admin role)
    cust_headers = {"Authorization": f"Bearer {cust1_token}"}
    res_forbidden = client.get("/api/customers", headers=cust_headers)
    print(f">> 1.2 Customer Access (Forbidden): HTTP {res_forbidden.status_code}")
    assert res_forbidden.status_code == 403

    # 1.3 Admin accessing customer list
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    res_admin = client.get("/api/customers", headers=admin_headers)
    print(f">> 1.3 Admin Access: HTTP {res_admin.status_code}")
    assert res_admin.status_code == 200
    customers = res_admin.json()
    assert len(customers) >= 2
    print(f"   Total customers retrieved: {len(customers)}")
    print(f"   Sample Customer: {customers[0]['full_name']} ({customers[0]['city']})")

    # 1.4 Filter by city
    res_city = client.get("/api/customers?city=Chennai", headers=admin_headers)
    assert res_city.status_code == 200
    chennai_custs = res_city.json()
    for c in chennai_custs:
        assert "Chennai" in c["city"]
    print(f">> 1.4 City Filter (?city=Chennai): Found {len(chennai_custs)} customers")


def test_get_customer_by_id(admin_token, cust1_token, cust2_token):
    print("\n[TEST SET 2] GET /api/customers/{id} - Retrieval & Access Control")
    print("-" * 75)

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    cust1_headers = {"Authorization": f"Bearer {cust1_token}"}
    cust2_headers = {"Authorization": f"Bearer {cust2_token}"}

    # 2.1 Customer 1 viewing own profile (customer_id 1)
    res_own = client.get("/api/customers/1", headers=cust1_headers)
    print(f">> 2.1 Customer 1 Viewing Own Profile: HTTP {res_own.status_code}")
    assert res_own.status_code == 200
    assert res_own.json()["full_name"] == "Arun Kumar"

    # 2.2 Customer 1 attempting to view Customer 2's profile (customer_id 2) -> 403 Forbidden
    res_other = client.get("/api/customers/2", headers=cust1_headers)
    print(f">> 2.2 Customer 1 Accessing Customer 2's Profile: HTTP {res_other.status_code} (Forbidden)")
    assert res_other.status_code == 403

    # 2.3 Admin viewing Customer 2's profile -> 200 OK
    res_admin_view = client.get("/api/customers/2", headers=admin_headers)
    print(f">> 2.3 Admin Viewing Customer 2's Profile: HTTP {res_admin_view.status_code}")
    assert res_admin_view.status_code == 200
    assert res_admin_view.json()["full_name"] == "Priya Sharma"

    # 2.4 Non-existent customer ID (EC-08) -> 404 Not Found
    res_404 = client.get("/api/customers/9999", headers=admin_headers)
    print(f">> 2.4 Non-Existent Customer ID (EC-08): HTTP {res_404.status_code} (Not Found)")
    assert res_404.status_code == 404
    assert res_404.json()["detail"] == "Customer not found."


def test_update_customer(admin_token, cust1_token):
    print("\n[TEST SET 3] PUT /api/customers/{id} - Profile Updates")
    print("-" * 75)

    cust1_headers = {"Authorization": f"Bearer {cust1_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3.1 Customer updating own city and address
    update_payload = {
        "address": "42, Residency Road, T. Nagar",
        "city": "Chennai"
    }
    res_update = client.put("/api/customers/1", json=update_payload, headers=cust1_headers)
    print(f">> 3.1 Customer Updating Own Profile: HTTP {res_update.status_code}")
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["address"] == "42, Residency Road, T. Nagar"
    print(f"   Updated Address: {updated_data['address']}")

    # 3.2 Invalid Phone update (EC-10) -> 422 Unprocessable Entity
    bad_phone = {"phone": "invalid_letters"}
    res_bad_phone = client.put("/api/customers/1", json=bad_phone, headers=cust1_headers)
    print(f">> 3.2 Update with Invalid Phone (EC-10): HTTP {res_bad_phone.status_code} (Rejected)")
    assert res_bad_phone.status_code == 422

    # 3.3 Update non-existent customer (EC-08) -> 404 Not Found
    res_404 = client.put("/api/customers/9999", json=update_payload, headers=admin_headers)
    print(f">> 3.3 Update Non-Existent Customer (EC-08): HTTP {res_404.status_code} (Not Found)")
    assert res_404.status_code == 404


def test_delete_customer(admin_token, cust1_token):
    print("\n[TEST SET 4] DELETE /api/customers/{id} - Deletion & Integrity Rules")
    print("-" * 75)

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    cust1_headers = {"Authorization": f"Bearer {cust1_token}"}

    # 4.1 Non-admin trying to delete a customer -> 403 Forbidden
    res_forbidden = client.delete("/api/customers/1", headers=cust1_headers)
    print(f">> 4.1 Non-Admin Attempting Delete: HTTP {res_forbidden.status_code} (Forbidden)")
    assert res_forbidden.status_code == 403

    # 4.2 Deleting customer with existing parcels (EC-11) -> 400 Bad Request
    res_with_parcels = client.delete("/api/customers/1", headers=admin_headers)
    print(f">> 4.2 Delete Customer with Existing Parcels (EC-11): HTTP {res_with_parcels.status_code} (Rejected)")
    assert res_with_parcels.status_code == 400
    assert "Cannot delete customer with existing parcels" in res_with_parcels.json()["detail"]
    print("   Successfully protected relational integrity!")

    # 4.3 Create a temporary customer with NO parcels, then delete successfully
    reg_temp = {
        "email": "temp_delete_user@pcts.com",
        "password": "Password123!",
        "role": "customer",
        "full_name": "Temporary Customer",
        "phone": "9876599999",
        "city": "Madurai"
    }
    res_reg = client.post("/api/auth/register", json=reg_temp)
    assert res_reg.status_code == 201
    temp_user_id = res_reg.json()["user_id"]

    db = SessionLocal()
    temp_customer = db.scalar(select(Customer).where(Customer.user_id == temp_user_id))
    temp_cust_id = temp_customer.customer_id
    db.close()

    # Now delete as admin
    res_del = client.delete(f"/api/customers/{temp_cust_id}", headers=admin_headers)
    print(f">> 4.3 Delete Customer with Zero Parcels: HTTP {res_del.status_code} (Success)")
    assert res_del.status_code == 200
    assert "Customer deleted successfully" in res_del.json()["message"]


if __name__ == "__main__":
    print("=" * 75)
    print("  PHASE 11: CUSTOMER MANAGEMENT CRUD AUTOMATED TEST SUITE")
    print("=" * 75)
    admin_tok, cust1_tok, cust2_tok = get_auth_tokens()
    test_list_customers(admin_tok, cust1_tok)
    test_get_customer_by_id(admin_tok, cust1_tok, cust2_tok)
    test_update_customer(admin_tok, cust1_tok)
    test_delete_customer(admin_tok, cust1_tok)
    print("\n" + "=" * 75)
    print("  ALL CUSTOMER MANAGEMENT CRUD & EDGE CASE TESTS PASSED!")
    print("=" * 75)
