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
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
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
# STARTUP: INITIALIZE DATABASE SCHEMA & ENSURE DEMO DATA
# -----------------------------------------------------------------------------
@app.on_event("startup")
def ensure_default_demo_users():
    """
    1. Synchronizes DB schema (Base.metadata.create_all).
    2. Ensures multiple standard demo accounts (Admins, Delivery Agents, Customers) exist.
    3. Seeds realistic demo shipments, milestone checkpoints, and payments if database is empty.
    """
    try:
        from backend.database import init_db_connection, SessionLocal
        from backend.models.user import User
        from backend.models.customer import Customer
        from backend.models.delivery_person import DeliveryPerson
        from backend.models.parcel import Parcel
        from backend.models.parcel_status import ParcelStatus
        from backend.models.delivery import Delivery
        from backend.models.payment import Payment
        from backend.security import hash_password, verify_password
        from sqlalchemy import select, func

        # 1. Initialize DB and create all tables if missing
        init_db_connection()

        # 2. Admins
        admins = [
            ("admin@pcts.com", "Admin@12345"),
            ("priya.admin@pcts.com", "Admin@12345"),
            ("vikram.admin@pcts.com", "Admin@12345")
        ]

        # 3. Delivery Agents
        agents = [
            ("ravi.delivery@pcts.com", "Delivery@12345", "Ravi Varma", "9876543333", "TN-01-AB-1234"),
            ("suresh.delivery@pcts.com", "Delivery@12345", "Suresh Patil", "9876543334", "MH-12-CD-5678"),
            ("anjali.delivery@pcts.com", "Delivery@12345", "Anjali Rao", "9876543335", "KA-05-EF-9012"),
            ("sunil.delivery@pcts.com", "Delivery@12345", "Sunil Das", "9876543336", "DL-01-GH-3456")
        ]

        # 4. Customers
        customers = [
            ("arun.kumar@gmail.com", "Customer@12345", "Arun Kumar", "9876543210", "12, 4th Main Road, Anna Nagar", "Chennai"),
            ("priya.sharma@yahoo.com", "Customer@12345", "Priya Sharma", "9876543222", "45, Palm Avenue, Whitefield", "Bengaluru"),
            ("kavita.nair@gmail.com", "Customer@12345", "Kavita Nair", "9876540001", "88, Marine Drive, Fort Kochi", "Kochi")
        ]

        db = SessionLocal()
        try:
            # Upsert Admins
            for email, pwd in admins:
                user = db.scalar(select(User).where(User.email == email))
                if not user:
                    user = User(email=email, password_hash=hash_password(pwd), role="admin")
                    db.add(user)
                elif not verify_password(pwd, user.password_hash):
                    user.password_hash = hash_password(pwd)
            db.flush()

            # Upsert Delivery Agents
            agent_map = {}
            for email, pwd, full_name, phone, vehicle in agents:
                user = db.scalar(select(User).where(User.email == email))
                if not user:
                    user = User(email=email, password_hash=hash_password(pwd), role="delivery")
                    db.add(user)
                    db.flush()
                elif not verify_password(pwd, user.password_hash):
                    user.password_hash = hash_password(pwd)
                
                agent = db.scalar(select(DeliveryPerson).where(DeliveryPerson.user_id == user.user_id))
                if not agent:
                    agent = DeliveryPerson(
                        user_id=user.user_id,
                        full_name=full_name,
                        phone=phone,
                        vehicle_number=vehicle,
                        is_active=True
                    )
                    db.add(agent)
                    db.flush()
                agent_map[email] = agent
            db.flush()

            # Upsert Customers
            customer_map = {}
            for email, pwd, full_name, phone, address, city in customers:
                user = db.scalar(select(User).where(User.email == email))
                if not user:
                    user = User(email=email, password_hash=hash_password(pwd), role="customer")
                    db.add(user)
                    db.flush()
                elif not verify_password(pwd, user.password_hash):
                    user.password_hash = hash_password(pwd)
                
                cust = db.scalar(select(Customer).where(Customer.user_id == user.user_id))
                if not cust:
                    cust = Customer(
                        user_id=user.user_id,
                        full_name=full_name,
                        phone=phone,
                        address=address,
                        city=city
                    )
                    db.add(cust)
                    db.flush()
                customer_map[email] = cust
            db.commit()

            # 5. Seed Demo Parcels if table is empty
            parcel_count = db.scalar(select(func.count(Parcel.parcel_id)))
            if parcel_count == 0:
                print("[Database] Seeding initial demo shipments, tracking milestones, and deliveries...")
                arun = customer_map.get("arun.kumar@gmail.com")
                priya = customer_map.get("priya.sharma@yahoo.com")
                ravi = agent_map.get("ravi.delivery@pcts.com")
                suresh = agent_map.get("suresh.delivery@pcts.com")

                if arun and priya and ravi and suresh:
                    demo_parcels = [
                        {
                            "tracking_id": "PCTS-20261114-1001",
                            "customer_id": arun.customer_id,
                            "sender_name": "Arun Kumar",
                            "sender_phone": "9876543210",
                            "receiver_name": "Kavita Nair",
                            "receiver_phone": "9876540001",
                            "receiver_address": "88, Marine Drive, Fort Kochi",
                            "source_city": "Chennai",
                            "destination_city": "Bengaluru",
                            "parcel_type": "Electronics",
                            "weight_kg": 2.50,
                            "description": "Smart Tablet and Accessories",
                            "charge": 150.00,
                            "status": "In Transit",
                            "location": "Vellore Transit Hub",
                            "agent": ravi,
                            "payment_method": "UPI",
                            "payment_status": "Paid"
                        },
                        {
                            "tracking_id": "PCTS-20261114-1002",
                            "customer_id": arun.customer_id,
                            "sender_name": "Arun Kumar",
                            "sender_phone": "9876543210",
                            "receiver_name": "Suresh Babu",
                            "receiver_phone": "9876540002",
                            "receiver_address": "15, Beach Road, Puducherry",
                            "source_city": "Chennai",
                            "destination_city": "Puducherry",
                            "parcel_type": "Document",
                            "weight_kg": 0.80,
                            "description": "Legal & University Certificates",
                            "charge": 60.00,
                            "status": "Booked",
                            "location": "Chennai Central Hub",
                            "agent": None,
                            "payment_method": "Cash on Delivery",
                            "payment_status": "Pending"
                        },
                        {
                            "tracking_id": "PCTS-20261114-1003",
                            "customer_id": priya.customer_id,
                            "sender_name": "Priya Sharma",
                            "sender_phone": "9876543222",
                            "receiver_name": "Deepak Verma",
                            "receiver_phone": "9876540003",
                            "receiver_address": "45, Palm Avenue, Whitefield",
                            "source_city": "Bengaluru",
                            "destination_city": "Chennai",
                            "parcel_type": "Fragile",
                            "weight_kg": 4.50,
                            "description": "Ceramic Dinnerware Set",
                            "charge": 220.00,
                            "status": "Out for Delivery",
                            "location": "Chennai South Delivery Depot",
                            "agent": ravi,
                            "payment_method": "Credit Card",
                            "payment_status": "Paid"
                        },
                        {
                            "tracking_id": "PCTS-20261114-1004",
                            "customer_id": priya.customer_id,
                            "sender_name": "Priya Sharma",
                            "sender_phone": "9876543222",
                            "receiver_name": "Ananya Sen",
                            "receiver_phone": "9876540004",
                            "receiver_address": "12, Jubilee Hills, Hyderabad",
                            "source_city": "Bengaluru",
                            "destination_city": "Hyderabad",
                            "parcel_type": "General",
                            "weight_kg": 8.00,
                            "description": "Reference Books and Journals",
                            "charge": 320.00,
                            "status": "Delivered",
                            "location": "Hyderabad Banjara Hills Hub",
                            "agent": suresh,
                            "payment_method": "Net Banking",
                            "payment_status": "Paid",
                            "delivered": True
                        }
                    ]

                    for p_data in demo_parcels:
                        p = Parcel(
                            tracking_id=p_data["tracking_id"],
                            customer_id=p_data["customer_id"],
                            sender_name=p_data["sender_name"],
                            sender_phone=p_data["sender_phone"],
                            receiver_name=p_data["receiver_name"],
                            receiver_phone=p_data["receiver_phone"],
                            receiver_address=p_data["receiver_address"],
                            source_city=p_data["source_city"],
                            destination_city=p_data["destination_city"],
                            parcel_type=p_data["parcel_type"],
                            weight_kg=p_data["weight_kg"],
                            description=p_data["description"],
                            charge=p_data["charge"],
                            booked_at=datetime.now()
                        )
                        db.add(p)
                        db.flush()

                        # Status
                        ps = ParcelStatus(
                            parcel_id=p.parcel_id,
                            status=p_data["status"],
                            location=p_data["location"],
                            updated_at=datetime.now()
                        )
                        db.add(ps)

                        # Delivery
                        if p_data["agent"]:
                            deliv = Delivery(
                                parcel_id=p.parcel_id,
                                delivery_person_id=p_data["agent"].delivery_person_id,
                                assigned_at=datetime.now(),
                                delivered_at=datetime.now() if p_data.get("delivered") else None
                            )
                            db.add(deliv)

                        # Payment
                        pay = Payment(
                            parcel_id=p.parcel_id,
                            amount=p_data["charge"],
                            payment_method=p_data["payment_method"],
                            payment_status=p_data["payment_status"],
                            paid_at=datetime.now() if p_data["payment_status"] == "Paid" else None
                        )
                        db.add(pay)

                    db.commit()
                    print(f"[Database] Successfully seeded {len(demo_parcels)} demo shipments.")

        finally:
            db.close()
    except Exception as e:
        print(f"[Warning] Demo data synchronization error: {e}")


# -----------------------------------------------------------------------------
# FRONTEND DIRECTORY PATH
# -----------------------------------------------------------------------------
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


# -----------------------------------------------------------------------------
# ENDPOINT 1: Root Website Entrypoint
# -----------------------------------------------------------------------------
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

@app.get(
    "/",
    summary="Root Website Home Page",
    include_in_schema=False
)
def read_root():
    """Serves the main frontend website index.html."""
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})
    return RedirectResponse(url="/static/index.html")


@app.get("/api-info", summary="API System Info", tags=["General"])
def api_welcome_info():
    """Returns basic system and documentation links as JSON."""
    return {
        "project": "Parcel and Courier Tracking System (PCTS)",
        "message": "Hello, PCTS! Welcome to the Parcel & Courier Tracking API.",
        "documentation": "/docs",
        "alternative_docs": "/redoc",
        "status": "online"
    }


@app.get("/{page_name}.html", include_in_schema=False)
def serve_html_page(page_name: str):
    """Directly serves any frontend HTML page (e.g. login.html, dashboard.html)."""
    file_path = os.path.join(frontend_dir, f"{page_name}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})
    raise HTTPException(status_code=404, detail=f"Page '{page_name}.html' not found.")


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
    and successfully query the database.
    """
    from backend.mongo import is_mongo_connected
    from backend.models.user import User
    from backend.models.parcel import Parcel
    from backend.database import engine

    mongo_status = "connected" if is_mongo_connected() else "offline"
    try:
        result = db.execute(text("SELECT 1 AS alive")).scalar()
        user_count = db.query(User).count()
        parcel_count = db.query(Parcel).count()
        return {
            "status": "connected" if result == 1 else "unresponsive",
            "dialect": engine.dialect.name,
            "host": engine.url.host or "local_sqlite",
            "database_url_configured": bool(os.getenv("DATABASE_URL")),
            "users_in_db": user_count,
            "parcels_in_db": parcel_count,
            "nosql_database": "MongoDB",
            "nosql_status": mongo_status
        }
    except Exception as e:
        return {
            "status": "error",
            "error_detail": str(e),
            "database_url_configured": bool(os.getenv("DATABASE_URL")),
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


# -----------------------------------------------------------------------------
# PHASE 19: FRONTEND STATIC PAGES & ASSETS
# -----------------------------------------------------------------------------
import os
from fastapi.staticfiles import StaticFiles

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    class FrontendStaticFiles(StaticFiles):
        async def get_response(self, path, scope):
            response = await super().get_response(path, scope)
            if path.endswith((".html", ".js")):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response

    app.mount("/static", FrontendStaticFiles(directory=frontend_dir, html=True), name="static")

    css_path = os.path.join(frontend_dir, "css")
    js_path = os.path.join(frontend_dir, "js")
    if os.path.exists(css_path):
        app.mount("/css", StaticFiles(directory=css_path), name="css")
    if os.path.exists(js_path):
        app.mount("/js", FrontendStaticFiles(directory=js_path), name="js")



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
        receiver_address=parcel_in.receiver_address,
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
