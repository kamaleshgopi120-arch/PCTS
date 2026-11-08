"""
Quick test script to verify backend is working
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("TESTING PCTS BACKEND SETUP")
print("=" * 60)

# Test 1: Environment variables
print("\n1. Testing Environment Variables...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    print(f"   ✓ DB_HOST: {db_host}")
    print(f"   ✓ DB_NAME: {db_name}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 2: MySQL Connection
print("\n2. Testing MySQL Connection...")
try:
    from backend.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DATABASE() as db"))
        db = result.fetchone()[0]
        print(f"   ✓ Connected to database: {db}")
        
        # Check tables
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        print(f"   ✓ Found {len(tables)} tables: {', '.join(tables[:5])}...")
        
        # Check sample data
        result = conn.execute(text("SELECT COUNT(*) FROM user"))
        user_count = result.fetchone()[0]
        print(f"   ✓ User table has {user_count} records")
        
        result = conn.execute(text("SELECT COUNT(*) FROM customer"))
        customer_count = result.fetchone()[0]
        print(f"   ✓ Customer table has {customer_count} records")
        
        result = conn.execute(text("SELECT COUNT(*) FROM parcel"))
        parcel_count = result.fetchone()[0]
        print(f"   ✓ Parcel table has {parcel_count} records")
except Exception as e:
    print(f"   ✗ MySQL Error: {e}")
    print("\n   Make sure:")
    print("   - MySQL server is running")
    print("   - Database 'pcts_db' exists")
    print("   - SQL scripts have been executed")
    sys.exit(1)

# Test 3: MongoDB Connection
print("\n3. Testing MongoDB Connection...")
try:
    from backend.mongo import get_mongo_db
    db = get_mongo_db()
    collections = db.list_collection_names()
    print(f"   ✓ Connected to MongoDB")
    print(f"   ✓ Collections: {collections if collections else 'None (will be created on first use)'}")
except Exception as e:
    print(f"   ✗ MongoDB Error: {e}")
    print("\n   Make sure MongoDB service is running")
    sys.exit(1)

# Test 4: Import all routers
print("\n4. Testing Backend Modules...")
try:
    from backend.main import app
    print(f"   ✓ FastAPI app loaded successfully")
    print(f"   ✓ App title: {app.title}")
except Exception as e:
    print(f"   ✗ Import Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - BACKEND IS READY!")
print("=" * 60)
print("\nYou can now start the server with:")
print("   python -m uvicorn backend.main:app --reload --port 8000")
print("\nThen open: http://127.0.0.1:8000/static/login.html")
print("=" * 60)
