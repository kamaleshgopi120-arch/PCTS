"""
backend/test_reports.py — Phase 17: Reports & Analytics Automated Test Suite
=============================================================================
Automated test suite verifying:
1. Role-based access control (Admin only, rejects non-admins with 403).
2. GET /api/reports/parcels: Status grouping, percentages, charges, and weight.
3. GET /api/reports/payments: Gross cash flow, collected vs pending amounts, and method breakdown.
4. GET /api/reports/deliveries: Courier workforce workload and completion rates.
5. GET /api/reports/monthly: Monthly executive summary with validation.
=============================================================================
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.main import app
from backend.database import SessionLocal
from backend.models.user import User
from backend.security import create_access_token

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

        return admin_tok, cust_tok, deliv_tok
    finally:
        db.close()


def run_tests():
    print_section("PHASE 17: REPORTS & ANALYTICS API AUTOMATED TEST SUITE")

    admin_tok, cust_tok, deliv_tok = get_test_tokens()
    auth_admin = {"Authorization": f"Bearer {admin_tok}"}
    auth_cust = {"Authorization": f"Bearer {cust_tok}"}
    auth_deliv = {"Authorization": f"Bearer {deliv_tok}"}

    # -------------------------------------------------------------------------
    # TEST SET 1: Role-Based Access Control (Admin Only)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 1] Access Control: Reports restricted exclusively to Admins")
    print("-" * 75)

    endpoints = [
        "/api/reports/parcels",
        "/api/reports/payments",
        "/api/reports/deliveries",
        f"/api/reports/monthly?year={datetime.now().year}&month={datetime.now().month}"
    ]

    for ep in endpoints:
        # 1.1 Without token -> 401 Unauthorized
        res_no_auth = client.get(ep)
        assert res_no_auth.status_code == 401, f"Expected 401 for {ep}, got {res_no_auth.status_code}"

        # 1.2 Customer accessing -> 403 Forbidden
        res_cust = client.get(ep, headers=auth_cust)
        assert res_cust.status_code == 403, f"Expected 403 for {ep}, got {res_cust.status_code}"

        # 1.3 Delivery agent accessing -> 403 Forbidden
        res_deliv = client.get(ep, headers=auth_deliv)
        assert res_deliv.status_code == 403, f"Expected 403 for {ep}, got {res_deliv.status_code}"

    print(">> 1.1 All report endpoints correctly rejected unauthorized requests (401).")
    print(">> 1.2 Customers correctly blocked with 403 Forbidden.")
    print(">> 1.3 Delivery agents correctly blocked with 403 Forbidden.")

    # -------------------------------------------------------------------------
    # TEST SET 2: Parcels Report (GET /api/reports/parcels)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 2] GET /api/reports/parcels - Parcel Aggregation by Status")
    print("-" * 75)

    res_parcels = client.get("/api/reports/parcels", headers=auth_admin)
    print(f">> 2.1 Admin Request: HTTP {res_parcels.status_code}")
    assert res_parcels.status_code == 200
    p_data = res_parcels.json()

    assert p_data["total_parcels"] > 0
    assert p_data["total_revenue"] > 0
    assert p_data["average_weight_kg"] > 0
    assert len(p_data["by_status"]) > 0

    print(f"    Total Parcels:        {p_data['total_parcels']}")
    print(f"    Total Revenue:        Rs. {p_data['total_revenue']:.2f}")
    print(f"    Average Weight:       {p_data['average_weight_kg']:.2f} kg")
    print("    Breakdown by Status:")
    total_pct = sum(item["percentage"] for item in p_data["by_status"])
    for s in p_data["by_status"]:
        print(f"      * {s['status']:<18} | Count: {s['count']:>2} ({s['percentage']:>5.1f}%) | Charges: Rs. {s['total_charges']:>7.2f} | Weight: {s['total_weight_kg']:>6.2f} kg")

    assert 99.0 <= total_pct <= 101.0, f"Percentages should sum to ~100%, got {total_pct}"
    print(">> 2.2 Status percentages correctly sum to ~100%.")

    # -------------------------------------------------------------------------
    # TEST SET 3: Payments Report (GET /api/reports/payments)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 3] GET /api/reports/payments - Financial Summary & Cash Flow")
    print("-" * 75)

    res_pay = client.get("/api/reports/payments", headers=auth_admin)
    print(f">> 3.1 Admin Request: HTTP {res_pay.status_code}")
    assert res_pay.status_code == 200
    pay_data = res_pay.json()

    assert pay_data["total_payments"] > 0
    assert pay_data["total_amount"] > 0
    assert pay_data["collected_amount"] >= 0
    assert pay_data["pending_amount"] >= 0
    assert len(pay_data["by_status"]) > 0

    print(f"    Total Payments:       {pay_data['total_payments']}")
    print(f"    Gross Amount:         Rs. {pay_data['total_amount']:.2f}")
    print(f"    Collected ('Paid'):   Rs. {pay_data['collected_amount']:.2f}")
    print(f"    Pending Settlement:   Rs. {pay_data['pending_amount']:.2f}")
    print("    Status Breakdown:")
    for ps in pay_data["by_status"]:
        print(f"      * {ps['payment_status']:<12} | Count: {ps['count']:>2} ({ps['percentage']:>5.1f}%) | Total: Rs. {ps['total_amount']:>7.2f}")
    print(f"    Revenue by Payment Method: {pay_data['by_method']}")

    # -------------------------------------------------------------------------
    # TEST SET 4: Deliveries Report (GET /api/reports/deliveries)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 4] GET /api/reports/deliveries - Courier Workforce Performance")
    print("-" * 75)

    res_deliv = client.get("/api/reports/deliveries", headers=auth_admin)
    print(f">> 4.1 Admin Request: HTTP {res_deliv.status_code}")
    assert res_deliv.status_code == 200
    d_data = res_deliv.json()

    assert d_data["total_deliveries"] >= 0
    assert len(d_data["agents"]) > 0

    print(f"    Total Assignments:    {d_data['total_deliveries']}")
    print(f"    Completed Deliveries: {d_data['total_delivered']}")
    print(f"    Overall Completion:   {d_data['overall_completion_rate']:.1f}%")
    print("    Agent Workloads:")
    for ag in d_data["agents"]:
        print(
            f"      * Agent #{ag['delivery_person_id']} {ag['full_name']} | "
            f"Assigned: {ag['assigned_count']} | Delivered: {ag['delivered_count']} | "
            f"Pending: {ag['pending_count']} | Rate: {ag['completion_rate']:.1f}%"
        )

    # -------------------------------------------------------------------------
    # TEST SET 5: Monthly Report (GET /api/reports/monthly)
    # -------------------------------------------------------------------------
    print("\n[TEST SET 5] GET /api/reports/monthly - Monthly Stored Procedure Summary")
    print("-" * 75)

    # 5.1 Invalid month parameters
    res_inv_mo = client.get("/api/reports/monthly?year=2026&month=13", headers=auth_admin)
    assert res_inv_mo.status_code == 422
    print(">> 5.1 Invalid Month (month=13) rejected with HTTP 422.")

    # 5.2 Current Month
    now = datetime.now()
    res_mo = client.get(f"/api/reports/monthly?year={now.year}&month={now.month}", headers=auth_admin)
    print(f">> 5.2 Monthly Report for {now.year}-{now.month:02d}: HTTP {res_mo.status_code}")
    assert res_mo.status_code == 200
    mo_data = res_mo.json()

    print(f"    Year:                 {mo_data['year']}, Month: {mo_data['month']}")
    print(f"    Parcels Booked:       {mo_data['total_parcels_booked']}")
    print(f"    Monthly Revenue:      Rs. {mo_data['total_revenue']:.2f}")
    print(f"    Average Weight:       {mo_data['average_weight_kg']:.2f} kg")
    print(f"    Status Breakdown:     {len(mo_data['by_status'])} statuses")
    print(f"    Destinations:         {len(mo_data['by_destination'])} destination cities")

    print("\n" + "=" * 75)
    print("  ALL REPORTS & ANALYTICS API TESTS PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
