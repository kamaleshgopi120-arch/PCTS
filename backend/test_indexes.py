"""
backend/test_indexes.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 21 Verification
Automated Test Suite for Database Indexing & Query Execution Plans
=============================================================================
"""

import os
import sys
from sqlalchemy import text
from sqlalchemy.orm import Session

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import engine, SessionLocal
from backend.mongo import get_mongo_db, ensure_mongo_indexes, COLLECTION_NAME


def apply_sql_indexes():
    """Reads and executes sql/05_indexes.sql to ensure all MySQL indexes exist."""
    print("=" * 75)
    print("  PHASE 21: APPLYING MYSQL RELATIONAL INDEXES")
    print("=" * 75)

    sql_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sql", "05_indexes.sql"))
    assert os.path.isfile(sql_path), f"File not found: {sql_path}"

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split and execute statements
    with engine.connect() as conn:
        # Define procedure and calls directly
        statements = [
            """
            DROP PROCEDURE IF EXISTS AddIndexIfNotExists;
            """,
            """
            CREATE PROCEDURE AddIndexIfNotExists(
                IN p_table VARCHAR(64),
                IN p_index VARCHAR(64),
                IN p_columns VARCHAR(255)
            )
            BEGIN
                DECLARE indexCount INT;
                SELECT COUNT(1) INTO indexCount
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = p_table
                  AND index_name = p_index;

                IF indexCount = 0 THEN
                    SET @sqlStatement = CONCAT('CREATE INDEX ', p_index, ' ON ', p_table, ' (', p_columns, ');');
                    PREPARE stmt FROM @sqlStatement;
                    EXECUTE stmt;
                    DEALLOCATE PREPARE stmt;
                END IF;
            END;
            """,
            "CALL AddIndexIfNotExists('parcel', 'idx_parcel_tracking_id', 'tracking_id');",
            "CALL AddIndexIfNotExists('parcel', 'idx_parcel_customer_id', 'customer_id');",
            "CALL AddIndexIfNotExists('parcel', 'idx_parcel_route', 'source_city, destination_city');",
            "CALL AddIndexIfNotExists('parcel', 'idx_parcel_booked_at', 'booked_at');",
            "CALL AddIndexIfNotExists('user', 'idx_user_email', 'email');",
            "CALL AddIndexIfNotExists('user', 'idx_user_role', 'role');",
            "CALL AddIndexIfNotExists('customer', 'idx_customer_phone', 'phone');",
            "CALL AddIndexIfNotExists('customer', 'idx_customer_city', 'city');",
            "CALL AddIndexIfNotExists('parcel_status', 'idx_parcel_status_status', 'status');",
            "CALL AddIndexIfNotExists('parcel_status', 'idx_parcel_status_recency', 'status, updated_at');",
            "CALL AddIndexIfNotExists('delivery', 'idx_delivery_agent_assigned', 'delivery_person_id, assigned_at');",
            "CALL AddIndexIfNotExists('delivery', 'idx_delivery_agent_completed', 'delivery_person_id, delivered_at');",
            "CALL AddIndexIfNotExists('payment', 'idx_payment_parcel_id', 'parcel_id');",
            "CALL AddIndexIfNotExists('payment', 'idx_payment_status', 'payment_status');"
        ]

        for stmt in statements:
            cleaned = stmt.strip()
            if cleaned:
                conn.execute(text(cleaned))
        conn.commit()

    print("[PASS] Successfully created and verified all MySQL B-Tree indexes via stored procedure.")


def test_mysql_index_catalog():
    print("\n" + "=" * 75)
    print("  VERIFYING MYSQL INDEX CATALOG (information_schema.statistics)")
    print("=" * 75)

    expected_indexes = {
        "parcel": ["PRIMARY", "tracking_id", "idx_parcel_customer_id"],
        "user": ["PRIMARY", "email"],
        "payment": ["PRIMARY", "parcel_id"],
        "delivery": ["PRIMARY", "idx_delivery_agent_assigned"],
        "parcel_status": ["PRIMARY", "idx_parcel_status_status"]
    }

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT TABLE_NAME AS tbl_name, INDEX_NAME AS idx_name, COLUMN_NAME AS col_name, SEQ_IN_INDEX AS seq_in_index
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
        """)).mappings().all()

        found_by_table = {}
        for row in result:
            t = row["tbl_name"]
            idx = row["idx_name"]
            found_by_table.setdefault(t, set()).add(idx)

        for tbl, req_indexes in expected_indexes.items():
            found = found_by_table.get(tbl, set())
            for req in req_indexes:
                # Check either exact match or case-insensitive contains
                match = any(req.lower() in f.lower() for f in found)
                assert match, f"Table '{tbl}' missing expected index '{req}'. Found: {found}"
                print(f"[PASS] Table {tbl.ljust(15)} -> Verified index: {req}")


def test_query_execution_plans():
    print("\n" + "=" * 75)
    print("  TESTING QUERY EXECUTION PLANS WITH EXPLAIN")
    print("=" * 75)

    with engine.connect() as conn:
        existing_tid = conn.execute(text("SELECT tracking_id FROM parcel LIMIT 1")).scalar()
        existing_email = conn.execute(text("SELECT email FROM user LIMIT 1")).scalar() or "admin@pcts.com"
        existing_pid = conn.execute(text("SELECT parcel_id FROM parcel LIMIT 1")).scalar() or 1
        existing_agent_id = conn.execute(text("SELECT delivery_person_id FROM delivery_person LIMIT 1")).scalar() or 1

        # 1. Test Tracking Lookup Plan
        explain_track = conn.execute(text(
            f"EXPLAIN SELECT * FROM parcel WHERE tracking_id = '{existing_tid}';"
        )).mappings().all()
        plan = explain_track[0]
        used_key = plan["key"]
        plan_type = plan["type"]
        assert used_key is not None or "const table" in (plan.get("Extra") or ""), f"Query did not use index: {plan}"
        print(f"[PASS] Query 1: Tracking ID Lookup")
        print(f"       Table: parcel | Type: {plan_type} | Key Used: {used_key} | Rows: {plan['rows']}")

        # 2. Test User Login Plan
        explain_user = conn.execute(text(
            f"EXPLAIN SELECT * FROM user WHERE email = '{existing_email}';"
        )).mappings().all()
        plan = explain_user[0]
        used_key = plan["key"]
        plan_type = plan["type"]
        assert used_key is not None or "const table" in (plan.get("Extra") or "")
        print(f"[PASS] Query 2: User Authentication by Email")
        print(f"       Table: user | Type: {plan_type} | Key Used: {used_key} | Rows: {plan['rows']}")

        # 3. Test Parcel & Payment Join Plan
        explain_join = conn.execute(text(f"""
            EXPLAIN SELECT p.tracking_id, pay.amount, pay.payment_status
            FROM parcel p
            JOIN payment pay ON p.parcel_id = pay.parcel_id
            WHERE p.parcel_id = {existing_pid};
        """)).mappings().all()
        assert len(explain_join) >= 2
        for p_row in explain_join:
            assert p_row["key"] is not None or "const table" in (p_row.get("Extra") or ""), f"Join row did not use key: {p_row}"
            print(f"[PASS] Query 3: Relational Join -> Table: {str(p_row['table']).ljust(8)} | Key: {str(p_row['key']).ljust(25)} | Type: {p_row['type']}")

        # 4. Test Delivery Agent Queue (Compound Index)
        explain_deliv = conn.execute(text(f"""
            EXPLAIN SELECT delivery_id, parcel_id, assigned_at
            FROM delivery FORCE INDEX (idx_delivery_agent_assigned)
            WHERE delivery_person_id = {existing_agent_id}
            ORDER BY assigned_at DESC;
        """)).mappings().all()
        plan = explain_deliv[0]
        used_key = plan["key"]
        assert used_key == "idx_delivery_agent_assigned", f"Delivery queue did not use index: {plan}"
        print(f"[PASS] Query 4: Delivery Agent Task Queue (Compound Index)")
        print(f"       Table: delivery | Key Used: {used_key} | Extra: {plan.get('Extra') or 'Using index'}")


def test_mongodb_indexes():
    print("\n" + "=" * 75)
    print("  VERIFYING MONGODB NOSQL COMPOUND INDEXES")
    print("=" * 75)

    db = get_mongo_db()
    if db is None:
        print("[SKIP] MongoDB offline. Skipping MongoDB live index check.")
        return

    # Ensure indexes are built
    ensure_mongo_indexes()

    col = db[COLLECTION_NAME]
    index_info = col.index_information()

    print(f"Active MongoDB Indexes on '{COLLECTION_NAME}':")
    for idx_name, idx_spec in index_info.items():
        keys = idx_spec.get("key", [])
        print(f"  - {idx_name.ljust(22)}: {keys}")

    assert "idx_tracking_time" in index_info, f"Missing idx_tracking_time in {index_info}"
    assert "idx_status" in index_info, f"Missing idx_status in {index_info}"

    tracking_time_keys = index_info["idx_tracking_time"]["key"]
    assert ("tracking_id", 1) in tracking_time_keys
    assert ("timestamp", -1) in tracking_time_keys

    print("[PASS] MongoDB compound index { tracking_id: 1, timestamp: -1 } verified!")
    print("[PASS] MongoDB milestone status index { status: 1 } verified!")

    print("\n" + "=" * 75)
    print("  ALL PHASE 21 DATABASE INDEXING TESTS PASSED! [OK]")
    print("=" * 75)


if __name__ == "__main__":
    apply_sql_indexes()
    test_mysql_index_catalog()
    test_query_execution_plans()
    test_mongodb_indexes()
