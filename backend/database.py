"""
backend/database.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 9
SQLAlchemy 2.0 Database Connection, Engine, Session, and Base Setup
=============================================================================

What is an ORM (Object-Relational Mapper)?
- An ORM maps SQL database tables directly to Python classes, and rows to class instances (objects).
- Instead of writing raw SQL strings like "SELECT * FROM parcel WHERE id = 1",
  we write Python code like: db.query(Parcel).filter(Parcel.parcel_id == 1).first().
- Benefits:
  1. Type safety and IDE autocompletion.
  2. SQL Injection prevention automatically built-in.
  3. Easy database migration across DBMS vendors.
  4. Automatic relationship resolution (e.g., parcel.customer.full_name).

Key SQLAlchemy Concepts in this file:
1. `create_engine`: Establishes the low-level connection pool to MySQL via PyMySQL.
2. `sessionmaker`: Factory that generates new `Session` objects for each HTTP request.
3. `DeclarativeBase`: Base class that all our ORM models will inherit from.
4. `get_db()`: FastAPI dependency generator that provides a database session to endpoints
   and guarantees the session is closed when the request finishes.
"""

import os
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "pcts_db")

fallback_sqlite_url = "sqlite:///pcts.db"

# If an explicit DATABASE_URL is set in .env or Render, use it;
# otherwise use URL.create to safely escape special characters in passwords (like '@').
raw_db_url = os.getenv("DATABASE_URL")
if raw_db_url:
    DATABASE_URL = raw_db_url
    if str(DATABASE_URL).startswith("mysql://"):
        DATABASE_URL = str(DATABASE_URL).replace("mysql://", "mysql+pymysql://", 1)
else:
    # On cloud platforms (Render, Railway, etc.), if DATABASE_URL is not set and host is localhost,
    # default to a local SQLite database to prevent connection refused crashes.
    if (os.getenv("RENDER") or os.getenv("PORT")) and DB_HOST in ("localhost", "127.0.0.1"):
        DATABASE_URL = fallback_sqlite_url
    else:
        DATABASE_URL = URL.create(
            drivername="mysql+pymysql",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME
        )

# Fix TiDB Cloud common mistake: if pointing to system 'sys' schema, rewrite to 'test'
if "tidbcloud.com" in str(DATABASE_URL).lower():
    DATABASE_URL = re.sub(r"/sys(\?|$)", r"/test\1", str(DATABASE_URL))

# Configure connect_args (SSL support for Cloud MySQL such as TiDB, Aiven, etc.)
connect_args = {}
url_str = str(DATABASE_URL).lower()
if url_str.startswith("mysql"):
    connect_args["connect_timeout"] = 10
    if "tidbcloud.com" in url_str or "aivencloud.com" in url_str or "ssl" in url_str:
        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx
elif url_str.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# 2. Create the SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600 if url_str.startswith("mysql") else -1,
    connect_args=connect_args,
    echo=False
)

# 3. Create the SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 4. Create the Declarative Base class
Base = declarative_base()


def init_db_connection():
    """
    Validates database connectivity on startup.
    If MySQL connection fails (e.g. invalid host, offline), falls back to SQLite
    to ensure zero-downtime and avoid 500 error crashes.
    Also executes Base.metadata.create_all to ensure all tables exist.
    """
    global engine, SessionLocal, DATABASE_URL

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[Database] Successfully connected to: {engine.url.drivername} ({engine.url.host or 'local'})")
    except Exception as e:
        print(f"[Database Warning] Connection to primary database failed: {e}")
        if not str(DATABASE_URL).startswith("sqlite"):
            print("[Database Warning] Activating SQLite fallback to ensure service availability.")
            fallback_url = fallback_sqlite_url
            DATABASE_URL = fallback_url
            engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
            SessionLocal.configure(bind=engine)

    # Ensure all tables exist in the connected database
    import backend.models  # Registers all models with Base.metadata
    Base.metadata.create_all(bind=engine)
    print("[Database] Schema synchronized (Base.metadata.create_all completed).")
    return engine


# 5. Dependency for FastAPI Endpoints (`get_db`)
def get_db():
    """
    FastAPI Dependency that yields an independent database session per request.
    Using `yield` ensures the session is ALWAYS closed in the `finally` block,
    preventing connection leaks to MySQL.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
