"""
backend/main.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 7
Introduction to FastAPI: Entrypoint and Core Endpoints
=============================================================================

What is FastAPI?
- FastAPI is a modern, high-performance web framework for building APIs with Python.
- It is based on standard Python type hints, Starlette (for web routing), and Pydantic (for data validation).
- It automatically generates interactive OpenAPI documentation at `/docs` and `/redoc`.

What is Uvicorn?
- Python code cannot listen to HTTP network sockets directly on its own without a web server.
- Uvicorn is an ASGI (Asynchronous Server Gateway Interface) web server implementation
  that receives HTTP requests from clients (browsers, mobile apps, curl) and forwards
  them to our FastAPI application.

How to run this server:
  uvicorn backend.main:app --reload --port 8000
"""

from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database import get_db

# -----------------------------------------------------------------------------
# Initialize the FastAPI Application
# -----------------------------------------------------------------------------
# Metadata passed here is automatically displayed on the Swagger UI (/docs) page.
app = FastAPI(
    title="Parcel and Courier Tracking System (PCTS) API",
    description=(
        "Production-ready backend API for booking, tracking, and managing parcel deliveries. "
        "Built with FastAPI, SQLAlchemy, MySQL, and MongoDB."
    ),
    version="1.0.0",
    docs_url="/docs",      # Interactive Swagger UI documentation URL
    redoc_url="/redoc"     # Alternative clean ReDoc documentation URL
)

# -----------------------------------------------------------------------------
# PHASE 18: GLOBAL EXCEPTION & EDGE CASE HANDLERS
# -----------------------------------------------------------------------------
from backend.exceptions import register_exception_handlers

register_exception_handlers(app)


# -----------------------------------------------------------------------------
# ENDPOINT 1: Root / Welcome Endpoint
# -----------------------------------------------------------------------------
@app.get(
    "/",
    summary="Root Welcome Endpoint",
    tags=["General"]
)
def read_root():
    """
    Returns a welcome message and basic links to the API documentation.
    """
    return {
        "project": "Parcel and Courier Tracking System (PCTS)",
        "message": "Hello, PCTS! Welcome to the Parcel & Courier Tracking API.",
        "documentation": "/docs",
        "alternative_docs": "/redoc",
        "status": "online"
    }


# -----------------------------------------------------------------------------
# ENDPOINT 2: Health Check Endpoint
# -----------------------------------------------------------------------------
@app.get(
    "/health",
    summary="Health and Readiness Check",
    tags=["System"]
)
def health_check():
    """
    Standard health check endpoint used by monitoring systems and load balancers
    to verify that the web service is responsive.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "framework": "FastAPI",
        "server": "Uvicorn ASGI"
    }


# -----------------------------------------------------------------------------
# ENDPOINT 3: System Overview / Architecture Information
# -----------------------------------------------------------------------------
@app.get(
    "/info",
    summary="Project and Architecture Overview",
    tags=["System"]
)
def system_info():
    """
    Returns high-level metadata about the system components.
    """
    return {
        "app_name": "Parcel and Courier Tracking System",
        "version": "1.0.0",
        "architecture": {
            "relational_db": "MySQL 8.0 (Structured entities & PL/SQL)",
            "nosql_db": "MongoDB (Tracking history events)",
            "orm": "SQLAlchemy 2.0",
            "validation": "Pydantic v2"
        },
        "authors": "PCTS Development Team"
    }


# -----------------------------------------------------------------------------
# ENDPOINT 4: Database Health & Connectivity Check (Phase 9)
# -----------------------------------------------------------------------------
@app.get(
    "/db-health",
    summary="Database Connectivity Check",
    tags=["System"]
)
def database_health_check(db: Session = Depends(get_db)):
    """
    Verifies that FastAPI can acquire a connection from the SQLAlchemy pool
    and successfully query the MySQL database.
    """
    result = db.execute(text("SELECT 1 AS alive")).scalar()
    from backend.mongo import is_mongo_connected
    mongo_status = "connected" if is_mongo_connected() else "offline"
    return {
        "database": "MySQL 8.0",
        "status": "connected" if result == 1 else "unresponsive",
        "orm": "SQLAlchemy 2.0",
        "nosql_database": "MongoDB",
        "nosql_status": mongo_status
    }


# -----------------------------------------------------------------------------
# PHASE 10: USER AUTHENTICATION & AUTHORIZATION ROUTER
# -----------------------------------------------------------------------------
from backend.routers.auth import router as auth_router

app.include_router(auth_router)


# -----------------------------------------------------------------------------
# PHASE 11: CUSTOMER MANAGEMENT ROUTER
# -----------------------------------------------------------------------------
from backend.routers.customers import router as customers_router

app.include_router(customers_router)


# -----------------------------------------------------------------------------
# PHASE 12: PARCEL BOOKING & MANAGEMENT ROUTER
# -----------------------------------------------------------------------------
from backend.routers.parcels import router as parcels_router

app.include_router(parcels_router)


# -----------------------------------------------------------------------------
# PHASE 13: PUBLIC PARCEL TRACKING ROUTER
# -----------------------------------------------------------------------------
from backend.routers.tracking import router as tracking_router

app.include_router(tracking_router)


# -----------------------------------------------------------------------------
# PHASE 15: DELIVERY MANAGEMENT ROUTER
# -----------------------------------------------------------------------------
from backend.routers.deliveries import router as deliveries_router

app.include_router(deliveries_router)


# -----------------------------------------------------------------------------
# PHASE 16: PAYMENT MANAGEMENT ROUTER
# -----------------------------------------------------------------------------
from backend.routers.payments import router as payments_router

app.include_router(payments_router)


# -----------------------------------------------------------------------------
# PHASE 17: REPORTS & ANALYTICS ROUTER
# -----------------------------------------------------------------------------
from backend.routers.reports import router as reports_router

app.include_router(reports_router)


# =============================================================================
# PHASE 8: PYDANTIC SCHEMA VALIDATION DEMONSTRATION ENDPOINTS
# =============================================================================
# These endpoints demonstrate how FastAPI automatically validates JSON request
# bodies against Pydantic models. If the client submits invalid data (e.g.,
# bad email, short password, non-numeric phone, weight <= 0, or same source &
# destination cities), FastAPI automatically rejects the request with HTTP 422
# Unprocessable Entity and an informative error breakdown.
# =============================================================================

from backend.schemas import (
    UserCreate,
    UserResponse,
    CustomerCreate,
    CustomerResponse,
    ParcelCreate,
    ParcelResponse,
    calculate_shipping_charge
)


@app.post(
    "/demo/users/register",
    response_model=UserResponse,
    status_code=201,
    summary="Validate User Registration Payload",
    tags=["Validation Demo"]
)
def demo_register_user(user_in: UserCreate):
    """
    Demonstrates Pydantic user validation:
    - Validates email format (EmailStr)
    - Enforces password length >= 8 characters (EC-06)
    - Validates allowed user roles (customer, admin, delivery)
    """
    # Simulate DB persistence and ID assignment
    return UserResponse(
        user_id=101,
        email=user_in.email,
        role=user_in.role,
        created_at=datetime.now()
    )


@app.post(
    "/demo/customers",
    response_model=CustomerResponse,
    status_code=201,
    summary="Validate Customer Profile Payload",
    tags=["Validation Demo"]
)
def demo_create_customer(customer_in: CustomerCreate):
    """
    Demonstrates Pydantic customer validation:
    - Enforces 10-14 digit numeric phone numbers without letters (EC-10)
    - Validates minimum name and city length
    """
    return CustomerResponse(
        customer_id=501,
        user_id=customer_in.user_id,
        full_name=customer_in.full_name,
        phone=customer_in.phone,
        address=customer_in.address,
        city=customer_in.city
    )


@app.post(
    "/demo/parcels/book",
    response_model=ParcelResponse,
    status_code=201,
    summary="Validate Parcel Booking Payload and Preview Charge",
    tags=["Validation Demo"]
)
def demo_book_parcel(parcel_in: ParcelCreate):
    """
    Demonstrates Pydantic parcel validation:
    - Enforces weight > 0 kg (EC-13)
    - Enforces source_city != destination_city (EC-15)
    - Automatically calculates official shipping charge based on weight tiers
    """
    computed_charge = calculate_shipping_charge(parcel_in.weight_kg)
    generated_tracking_id = f"PCTS-{datetime.now().strftime('%Y%m%d')}-0001"

    return ParcelResponse(
        parcel_id=901,
        tracking_id=generated_tracking_id,
        customer_id=parcel_in.customer_id,
        sender_name=parcel_in.sender_name,
        sender_phone=parcel_in.sender_phone,
        receiver_name=parcel_in.receiver_name,
        receiver_phone=parcel_in.receiver_phone,
        source_city=parcel_in.source_city,
        destination_city=parcel_in.destination_city,
        parcel_type=parcel_in.parcel_type.value,
        weight_kg=parcel_in.weight_kg,
        description=parcel_in.description,
        charge=computed_charge,
        booked_at=datetime.now(),
        status="Booked",
        location=f"{parcel_in.source_city} Booking Office"
    )


# -----------------------------------------------------------------------------
# Direct Execution Support
# -----------------------------------------------------------------------------
# Allows running the application directly with:
#   python backend/main.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("Starting PCTS FastAPI server on http://127.0.0.1:8000 ...")
    print("Interactive Documentation available at http://127.0.0.1:8000/docs")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
