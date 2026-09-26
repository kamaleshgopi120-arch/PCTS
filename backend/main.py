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
from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
