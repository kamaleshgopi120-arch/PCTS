"""
08_mysql_raw.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 5
Demonstration: Connecting Python to MySQL using Raw SQL (PyMySQL)
=============================================================================

What you learn in this script:
1. How Python talks to MySQL over a network connection (TCP/IP on port 3306).
2. How to securely load credentials from a .env file using `python-dotenv`.
3. What a database Connection and a Cursor are.
4. Using `DictCursor` to get results as clean Python dictionaries {column: value}.
5. Executing parameterized queries (%s placeholder) to PREVENT SQL INJECTION.
6. Handling database transactions (commit and rollback).
7. Proper error handling with pymysql.MySQLError and resource cleanup.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import pymysql
import pymysql.cursors

# -----------------------------------------------------------------------------
# STEP 1: Load Environment Variables from .env
# -----------------------------------------------------------------------------
# NEVER hardcode passwords in your Python files!
# `load_dotenv()` looks for a `.env` file in the current directory or parents
# and loads its variables into Python's `os.environ`.
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "pcts_db")

print("=" * 70)
print("  PCTS DATABASE DEMO - PYTHON & RAW MYSQL (PyMySQL)")
print("=" * 70)
print(f"Connecting to MySQL host: {DB_HOST}:{DB_PORT} as user: {DB_USER}")
print(f"Target Database: {DB_NAME}")
print("=" * 70)


# -----------------------------------------------------------------------------
# Helper function to get a clean connection
# -----------------------------------------------------------------------------
def get_db_connection(use_database=True):
    """
    Creates and returns a new MySQL database connection.
    If use_database is False, connects to the server without selecting a DB.
    """
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if use_database else None,
        charset="utf8mb4",
        # DictCursor returns rows as Python dicts: {'col_name': value}
        # Standard cursor returns rows as tuples: (val1, val2)
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False  # Explicit transaction management
    )


# -----------------------------------------------------------------------------
# DEMO 1: Test Server Connection & Server Info
# -----------------------------------------------------------------------------
def test_connection():
    print("\n[DEMO 1] Testing Connection & Inspecting MySQL Server")
    print("-" * 70)
    try:
        conn = get_db_connection(use_database=True)
        print(">> Connection established successfully!")
        print(f">> MySQL Server Version: {conn.get_server_info()}")
        print(f">> Client Encoding:     {conn.character_set_name()}")
        conn.close()
    except pymysql.MySQLError as err:
        print(f">> Connection failed: {err}")
        raise


# -----------------------------------------------------------------------------
# DEMO 2: Fetch and Display All Parcels (DictCursor)
# -----------------------------------------------------------------------------
def fetch_all_parcels():
    print("\n[DEMO 2] Fetching Parcels from `parcel` Table")
    print("-" * 70)
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Query all parcels with their sender and receiver details
            sql = """
                SELECT tracking_id, sender_name, receiver_name,
                       destination_city, weight_kg, charge, parcel_type
                FROM parcel
                ORDER BY parcel_id ASC;
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            print(f"Total parcels found: {len(rows)}\n")
            print(f"{'Tracking ID':<20} {'Sender':<15} {'Receiver':<15} {'Destination':<12} {'Weight':<8} {'Charge':<10}")
            print("-" * 85)
            for row in rows:
                print(
                    f"{row['tracking_id']:<20} "
                    f"{row['sender_name']:<15} "
                    f"{row['receiver_name']:<15} "
                    f"{row['destination_city']:<12} "
                    f"{str(row['weight_kg']) + ' kg':<8} "
                    f"Rs. {row['charge']:<8.2f}"
                )
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# DEMO 3: Parameterized Query (SQL Injection Safe Tracking Search)
# -----------------------------------------------------------------------------
def search_parcel_by_tracking_id(tracking_code: str):
    """
    CRITICAL CONCEPT: Parameterized Queries
    NEVER DO THIS:
      cursor.execute(f"SELECT * FROM parcel WHERE tracking_id = '{tracking_code}'")
      -- An attacker could pass: "' OR '1'='1" and dump the entire database!

    ALWAYS DO THIS:
      cursor.execute("SELECT * FROM parcel WHERE tracking_id = %s", (tracking_code,))
      -- The DB driver escapes and treats `tracking_code` strictly as a raw string literal.
    """
    print(f"\n[DEMO 3] Searching for Parcel: '{tracking_code}' (Safe Parameterized Query)")
    print("-" * 70)
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT p.tracking_id, p.sender_name, p.receiver_name,
                       p.source_city, p.destination_city, p.weight_kg,
                       p.charge, ps.status, ps.location, ps.updated_at
                FROM parcel p
                INNER JOIN parcel_status ps ON p.parcel_id = ps.parcel_id
                WHERE p.tracking_id = %s;
            """
            cursor.execute(sql, (tracking_code,))
            result = cursor.fetchone()

            if result:
                print(">> Parcel Details Found:")
                print(f"   Tracking ID:  {result['tracking_id']}")
                print(f"   From:         {result['source_city']} ({result['sender_name']})")
                print(f"   To:           {result['destination_city']} ({result['receiver_name']})")
                print(f"   Weight:       {result['weight_kg']} kg")
                print(f"   Charge:       Rs. {result['charge']:.2f}")
                print(f"   Status:       {result['status']}")
                print(f"   Location:     {result['location']}")
                print(f"   Last Update:  {result['updated_at']}")
            else:
                print(f">> No parcel found with Tracking ID: {tracking_code}")
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# DEMO 4: Relational JOIN - Tracking Summary with Payment and Delivery
# -----------------------------------------------------------------------------
def full_tracking_report():
    print("\n[DEMO 4] Master 6-Table Relational JOIN (Active Pipeline)")
    print("-" * 70)
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    p.tracking_id,
                    c.full_name AS customer,
                    p.destination_city AS dest,
                    ps.status AS current_status,
                    COALESCE(dp.full_name, 'Unassigned') AS agent,
                    pay.payment_status AS payment
                FROM parcel p
                INNER JOIN customer c ON p.customer_id = c.customer_id
                INNER JOIN parcel_status ps ON p.parcel_id = ps.parcel_id
                LEFT JOIN delivery d ON p.parcel_id = d.parcel_id
                LEFT JOIN delivery_person dp ON d.delivery_person_id = dp.delivery_person_id
                INNER JOIN payment pay ON p.parcel_id = pay.parcel_id
                ORDER BY p.parcel_id ASC;
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            print(f"{'Tracking ID':<20} {'Customer':<15} {'Dest':<12} {'Status':<18} {'Agent':<15} {'Payment':<10}")
            print("-" * 95)
            for r in rows:
                print(
                    f"{r['tracking_id']:<20} "
                    f"{r['customer']:<15} "
                    f"{r['dest']:<12} "
                    f"{r['current_status']:<18} "
                    f"{r['agent']:<15} "
                    f"{r['payment']:<10}"
                )
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# DEMO 5: Transactions - Booking a New Parcel (Atomic Multi-Table Insert)
# -----------------------------------------------------------------------------
def book_new_parcel_transaction():
    """
    CRITICAL CONCEPT: Database Transactions (ACID properties)
    When booking a parcel, we must insert:
    1. A row into `parcel`
    2. An initial row into `parcel_status` ('Booked')
    3. An initial row into `payment` ('Pending')

    If step 3 fails, steps 1 and 2 must ROLLBACK so no orphan records exist!
    If all 3 succeed, we COMMIT the transaction.
    """
    print("\n[DEMO 5] Atomic Multi-Table Transaction (Booking Parcel + Status + Payment)")
    print("-" * 70)
    conn = get_db_connection()
    new_tracking_id = f"PCTS-{datetime.now().strftime('%Y%m%d')}-9999"

    try:
        with conn.cursor() as cursor:
            # 1. Insert into parcel
            # 4.2 kg parcel -> (1.01-5kg tier: Rs. 30/kg) = Rs. 126.00
            weight = 4.20
            charge = round(weight * 30.0, 2)

            sql_parcel = """
                INSERT INTO parcel (
                    tracking_id, customer_id, sender_name, sender_phone,
                    receiver_name, receiver_phone, source_city, destination_city,
                    parcel_type, weight_kg, description, charge
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(sql_parcel, (
                new_tracking_id, 1, "Arun Kumar", "9876543210",
                "Vikram Seth", "9876549999", "Chennai", "Coimbatore",
                "Electronics", weight, "Scientific Calculator & Accessories", charge
            ))
            # Retrieve the auto-generated parcel_id
            parcel_id = cursor.lastrowid
            print(f">> Step 1: Inserted parcel record (Generated parcel_id: {parcel_id})")

            # 2. Insert into parcel_status
            sql_status = """
                INSERT INTO parcel_status (parcel_id, status, location)
                VALUES (%s, %s, %s);
            """
            cursor.execute(sql_status, (parcel_id, "Booked", "Chennai Central Hub"))
            print(f">> Step 2: Inserted initial status 'Booked'")

            # 3. Insert into payment
            sql_payment = """
                INSERT INTO payment (parcel_id, amount, payment_method, payment_status)
                VALUES (%s, %s, %s, %s);
            """
            cursor.execute(sql_payment, (parcel_id, charge, "UPI", "Pending"))
            print(f">> Step 3: Inserted pending payment record (Rs. {charge:.2f})")

            # ALL 3 statements succeeded -> COMMIT!
            conn.commit()
            print(f">> Transaction COMMITTED successfully! Tracking ID: {new_tracking_id}")

        # Clean up this demo record to keep sample database pristine
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM parcel WHERE parcel_id = %s;", (parcel_id,))
            conn.commit()
            print(f">> (Cleaned up temporary demo record {new_tracking_id})")

    except pymysql.MySQLError as err:
        conn.rollback()
        print(f">> Transaction FAILED and was ROLLED BACK! Error: {err}")
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# MAIN EXECUTION FLOW
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    test_connection()
    fetch_all_parcels()
    search_parcel_by_tracking_id("PCTS-20240925-0003")
    search_parcel_by_tracking_id("PCTS-INVALID-9999")  # Edge case test
    full_tracking_report()
    book_new_parcel_transaction()

    print("\n" + "=" * 70)
    print("  PHASE 5 PYTHON MYSQL DEMO COMPLETE - ALL TESTS PASSED!")
    print("=" * 70)
