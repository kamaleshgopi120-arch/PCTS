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
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "pcts_db")

# If an explicit DATABASE_URL is set in .env, use it;
# otherwise use URL.create to safely escape special characters in passwords (like '@').
raw_db_url = os.getenv("DATABASE_URL")
if raw_db_url:
    DATABASE_URL = raw_db_url
    if str(DATABASE_URL).startswith("mysql://"):
        DATABASE_URL = str(DATABASE_URL).replace("mysql://", "mysql+pymysql://", 1)
else:
    DATABASE_URL = URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME
    )

# Configure connect_args (SSL support for Cloud MySQL such as TiDB, Aiven, etc.)
connect_args = {"connect_timeout": 10}
url_str = str(DATABASE_URL).lower()
if "tidbcloud.com" in url_str or "aivencloud.com" in url_str or "ssl" in url_str:
    import ssl
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_ctx

# 2. Create the SQLAlchemy Engine
# `pool_pre_ping=True`: Checks if a MySQL connection is alive before using it.
# `pool_size=5`, `max_overflow=10`: Controls the connection pool capacity.
# `connect_timeout=10`: Prevents indefinite hangs if database is offline.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour to avoid MySQL timeout
    connect_args=connect_args,
    echo=False          # Set to True if you want to see every raw SQL statement in the terminal
)

# 3. Create the SessionLocal class
# Each instance of SessionLocal is a database conversation/transaction.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 4. Create the Declarative Base class
# All database models in backend/models/ will inherit from this Base.
Base = declarative_base()


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
