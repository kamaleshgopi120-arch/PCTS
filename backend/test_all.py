"""
backend/test_all.py
=============================================================================
Parcel and Courier Tracking System (PCTS) — Phase 22 Master Test Runner
Orchestrates and executes all automated test suites across all phases.
=============================================================================
"""

import os
import sys
import time
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_EXE = sys.executable

TEST_SUITES = [
    {
        "name": "Workflow Rules: Pricing, Weights & Status Transitions",
        "script": "backend/test_workflow_rules.py"
    },
    {
        "name": "Phase 07: FastAPI Core & System Endpoints",
        "script": "backend/test_app.py"
    },
    {
        "name": "Phase 08: Pydantic Schema Validation",
        "script": "backend/test_schemas.py"
    },
    {
        "name": "Phase 09: SQLAlchemy Models & MySQL Pool",
        "script": "backend/test_database.py"
    },
    {
        "name": "Phase 10: Authentication, JWT & RBAC",
        "script": "backend/test_auth.py"
    },
    {
        "name": "Phase 11: Customer Management API",
        "script": "backend/test_customers.py"
    },
    {
        "name": "Phase 12: Parcel Booking & Pricing API",
        "script": "backend/test_parcels.py"
    },
    {
        "name": "Phase 13: Public Parcel Tracking API",
        "script": "backend/test_tracking.py"
    },
    {
        "name": "Phase 14: MongoDB NoSQL Event Store",
        "script": "backend/test_mongo.py"
    },
    {
        "name": "Phase 15: Delivery Management API",
        "script": "backend/test_deliveries.py"
    },
    {
        "name": "Phase 16: Payment Settlement & Surcharges",
        "script": "backend/test_payments.py"
    },
    {
        "name": "Phase 17: Reports & Analytics Procedures",
        "script": "backend/test_reports.py"
    },
    {
        "name": "Phase 18: Centralized Exception Handling",
        "script": "backend/test_exceptions.py"
    },
    {
        "name": "Phase 19: Frontend Static Pages & CSS System",
        "script": "backend/test_frontend.py"
    },
    {
        "name": "Phase 20: Frontend JavaScript Integration",
        "script": "backend/test_frontend_js.py"
    },
    {
        "name": "Phase 21: Database Indexing & EXPLAIN Plans",
        "script": "backend/test_indexes.py"
    },
    {
        "name": "Phase 22: Full Lifecycle E2E Integration",
        "script": "backend/test_e2e_integration.py"
    }
]


def run_master_test_suite():
    print("=" * 85)
    print("  PARCEL AND COURIER TRACKING SYSTEM (PCTS) — MASTER TEST SUITE")
    print(f"  Target Environment: Python {sys.version.split()[0]} | Project: {PROJECT_ROOT}")
    print("=" * 85)

    results = []
    total_start = time.time()

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    for idx, suite in enumerate(TEST_SUITES, 1):
        name = suite["name"]
        script_path = os.path.join(PROJECT_ROOT, suite["script"])

        if not os.path.isfile(script_path):
            print(f"[{idx:02d}/{len(TEST_SUITES)}] {name.ljust(50)} -> [MISSING SCRIPT]")
            results.append({"name": name, "status": "FAIL", "duration": 0.0, "error": "Script not found"})
            continue

        print(f"\n>> [{idx:02d}/{len(TEST_SUITES)}] RUNNING: {name} ({suite['script']})")
        start_t = time.time()

        proc = subprocess.run(
            [PYTHON_EXE, script_path],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env=env
        )

        duration = time.time() - start_t
        is_pass = proc.returncode == 0
        status_str = "PASS" if is_pass else "FAIL"

        results.append({
            "name": name,
            "script": suite["script"],
            "status": status_str,
            "duration": duration,
            "output": proc.stdout,
            "error": proc.stderr
        })

        if is_pass:
            print(f"   Result: [PASS] ({duration:.2f}s)")
        else:
            print(f"   Result: [FAIL] ({duration:.2f}s) (Exit Code: {proc.returncode})")
            if proc.stderr:
                print("   Error Traceback:")
                for line in proc.stderr.strip().split("\n")[-6:]:
                    print(f"     {line}")

    total_duration = time.time() - total_start

    # -------------------------------------------------------------------------
    # SUMMARY REPORT CARD
    # -------------------------------------------------------------------------
    print("\n\n" + "=" * 85)
    print("                          PCTS TEST MATRIX SUMMARY REPORT")
    print("=" * 85)
    print(f"{'#':<4} {'Test Suite / Component':<52} {'Time (s)':<12} {'Status'}")
    print("-" * 85)

    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed_count = sum(1 for r in results if r["status"] == "FAIL")

    for idx, r in enumerate(results, 1):
        status_label = "[PASS]" if r["status"] == "PASS" else "[FAIL]"
        print(f"{idx:<4} {r['name']:<52} {r['duration']:>7.2f}s     {status_label}")

    print("-" * 85)
    print(f"Total Suites : {len(results)}")
    print(f"Passed       : {passed_count} / {len(results)} ({(passed_count / len(results) * 100):.1f}%)")
    print(f"Failed       : {failed_count}")
    print(f"Total Time   : {total_duration:.2f} seconds")
    print("=" * 85)

    if failed_count == 0:
        print(f"\n[OK] ALL {len(TEST_SUITES)} TEST SUITES PASSED FLAWLESSLY! ZERO REGRESSIONS DETECTED. [OK]\n")
        sys.exit(0)
    else:
        print(f"\n[FAIL] {failed_count} TEST SUITE(S) FAILED. Please review the error logs above.\n")
        sys.exit(1)


if __name__ == "__main__":
    run_master_test_suite()
