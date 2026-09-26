"""
backend/test_app.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 7
Automated Verification for FastAPI Initialization and Endpoints
=============================================================================
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_endpoints():
    print("=" * 70)
    print("  FASTAPI ENDPOINT VERIFICATION (PHASE 7)")
    print("=" * 70)

    # 1. Test Root Endpoint
    response = client.get("/")
    print(f">> GET /  --> Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print(f"   Payload: {data}")
    assert data["status"] == "online"
    assert "Hello, PCTS!" in data["message"]

    # 2. Test Health Endpoint
    response = client.get("/health")
    print(f"\n>> GET /health  --> Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print(f"   Payload: {data}")
    assert data["status"] == "healthy"

    # 3. Test System Info Endpoint
    response = client.get("/info")
    print(f"\n>> GET /info  --> Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print(f"   Payload: {data}")
    assert data["version"] == "1.0.0"

    # 4. Test OpenAPI Schema (/openapi.json)
    response = client.get("/openapi.json")
    print(f"\n>> GET /openapi.json  --> Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    schema = response.json()
    print(f"   OpenAPI Version: {schema.get('openapi')}")
    print(f"   API Title: {schema.get('info', {}).get('title')}")
    assert "PCTS" in schema.get("info", {}).get("title")

    # 5. Test Swagger Docs UI (/docs)
    response = client.get("/docs")
    print(f"\n>> GET /docs  --> Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    print("\n" + "=" * 70)
    print("  ALL FASTAPI TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_endpoints()
