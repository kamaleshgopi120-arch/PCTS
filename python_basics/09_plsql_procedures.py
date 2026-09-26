"""
09_plsql_procedures.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 6
Demonstration: Calling PL/SQL Components from Python (PyMySQL)
=============================================================================

What you learn in this script:
1. How to invoke MySQL Stored Functions inside a Python SQL query.
2. How to call Stored Procedures using `cursor.execute("CALL ...")` and retrieve OUT parameters.
3. How to verify that a Database Trigger (`AFTER UPDATE`) fired automatically.
4. How to consume multiple result sets returned by a Stored Procedure using `cursor.nextset()`.
5. How DBMS PL/SQL components offload business logic to the database server.
"""

import os
from dotenv import load_dotenv
import pymysql
import pymysql.cursors

# Load database credentials from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "pcts_db")

print("=" * 75)
print("  PCTS PL/SQL DEMO - CALLING PROCEDURES, FUNCTIONS & TRIGGERS FROM PYTHON")
print("=" * 75)


def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


# -----------------------------------------------------------------------------
# DEMO 1: Calling the Stored Function `calculate_charge`
# -----------------------------------------------------------------------------
def demo_stored_function():
    print("\n[DEMO 1] Calling Stored Function: `calculate_charge(weight_kg)`")
    print("-" * 75)
    print("Stored functions return a single scalar value and can be embedded")
    print("directly in SQL SELECT statements.\n")

    test_weights = [0.50, 2.50, 8.00, 25.00]
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for w in test_weights:
                sql = "SELECT calculate_charge(%s) AS charge;"
                cursor.execute(sql, (w,))
                row = cursor.fetchone()
                charge = row["charge"]
                print(f"Weight: {w:>5.2f} kg  -->  Calculated Delivery Charge: Rs. {charge:>6.2f}")
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# DEMO 2: Calling Stored Procedure `update_parcel_status`
# -----------------------------------------------------------------------------
def demo_stored_procedure_update():
    print("\n[DEMO 2] Calling Stored Procedure: `update_parcel_status`")
    print("-" * 75)
    print("This procedure updates status, refreshes location, updates delivered_at")
    print("and automatically triggers the audit log.\n")

    tracking_code = "PCTS-20240925-0001"
    new_status = "In Transit"
    new_location = "Vellore Sorting Depot"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # We call the procedure with session variables @affected and @msg for OUT parameters
            sql = "CALL update_parcel_status(%s, %s, %s, @p_affected, @p_msg);"
            cursor.execute(sql, (tracking_code, new_status, new_location))

            # Retrieve OUT parameters
            cursor.execute("SELECT @p_affected AS affected, @p_msg AS message;")
            out_params = cursor.fetchone()

            print(f">> Procedure Call Result:")
            print(f"   Rows Affected: {out_params['affected']}")
            print(f"   Status Msg:    {out_params['message']}")
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# DEMO 3: Verifying the Database Trigger `trg_after_status_update`
# -----------------------------------------------------------------------------
def demo_verify_trigger():
    print("\n[DEMO 3] Verifying Database Trigger: `trg_after_status_update`")
    print("-" * 75)
    print("The trigger fired AUTOMATICALLY behind the scenes when the status was updated.")
    print("Let's query the `parcel_status_audit` table to prove it!\n")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT a.audit_id, p.tracking_id, a.old_status, a.new_status,
                       a.old_location, a.new_location, a.changed_at, a.changed_by
                FROM parcel_status_audit a
                INNER JOIN parcel p ON a.parcel_id = p.parcel_id
                ORDER BY a.audit_id DESC
                LIMIT 3;
            """
            cursor.execute(sql)
            audits = cursor.fetchall()

            print(f"{'Audit ID':<10} {'Tracking ID':<20} {'Old -> New Status':<28} {'Location':<25}")
            print("-" * 85)
            for a in audits:
                status_change = f"{a['old_status']} -> {a['new_status']}"
                loc_change = f"{a['new_location']}"
                print(f"{a['audit_id']:<10} {a['tracking_id']:<20} {status_change:<28} {loc_change:<25}")
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# DEMO 4: Stored Procedure with Multiple Result Sets `get_monthly_report`
# -----------------------------------------------------------------------------
def demo_monthly_report():
    print("\n[DEMO 4] Calling Stored Procedure: `get_monthly_report(year, month)`")
    print("-" * 75)
    print("Some stored procedures return multiple SELECT result sets.")
    print("In Python, we cycle through them using `cursor.nextset()`.\n")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("CALL get_monthly_report(%s, %s);", (2024, 9))

            # Result Set 1: High-Level Overview
            summary = cursor.fetchone()
            print(">> [Result Set 1: Monthly Overview]")
            print(f"   Period:           {summary['report_month']}/{summary['report_year']}")
            print(f"   Total Bookings:   {summary['total_parcels_booked']}")
            print(f"   Total Revenue:    Rs. {summary['total_revenue']:.2f}")
            print(f"   Avg Parcel Weight:{summary['average_weight_kg']} kg\n")

            # Move to Result Set 2: Status Breakdown
            if cursor.nextset():
                status_rows = cursor.fetchall()
                print(">> [Result Set 2: Breakdown by Current Status]")
                for r in status_rows:
                    print(f"   - {r['parcel_status']:<18} Count: {r['count_in_status']:<4} Revenue: Rs. {r['revenue_for_status']:.2f}")
                print()

            # Move to Result Set 3: Destination City Breakdown
            if cursor.nextset():
                city_rows = cursor.fetchall()
                print(">> [Result Set 3: Breakdown by Destination City]")
                for r in city_rows:
                    print(f"   - {r['destination_city']:<18} Parcels: {r['parcel_count']:<4} Revenue: Rs. {r['city_revenue']:.2f}")
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# MAIN DRIVER
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    demo_stored_function()
    demo_stored_procedure_update()
    demo_verify_trigger()
    demo_monthly_report()

    print("\n" + "=" * 75)
    print("  PHASE 6 PL/SQL DEMONSTRATION COMPLETE - ALL COMPONENTS TESTED!")
    print("=" * 75)
