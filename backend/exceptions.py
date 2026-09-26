"""
backend/exceptions.py — Global Exception Handlers & Error Normalization
=============================================================================
This module configures centralized, graceful error handling for the PCTS API.

Implements Edge Cases from edge_case.md:
- EC-34: Database connection failure -> 503 Service Unavailable.
- EC-36: Unique constraint violation -> 400 Bad Request ("This value already exists.").
- EC-37: Foreign key constraint violation -> 400 Bad Request ("Referenced record not found.").
- EC-38: Transaction failure midway -> Automatic rollback & safe 500 error.
- EC-39, EC-40, EC-41, EC-42: Schema and JSON validation errors formatted clearly.
=============================================================================
"""

import logging
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from pymysql.constants import ER

logger = logging.getLogger("pcts.exceptions")


def format_validation_error(exc: RequestValidationError) -> str:
    """Extracts human-readable summary of validation errors."""
    messages = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []) if l != "body")
        msg = err.get("msg", "Invalid value")
        # Remove redundant Pydantic prefix if present
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        if loc:
            messages.append(f"{loc}: {msg}")
        else:
            messages.append(msg)
    return "; ".join(messages)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers global exception handlers onto the FastAPI application instance."""

    # -------------------------------------------------------------------------
    # 1. Pydantic Request Validation Handler (EC-39, EC-40, EC-41, EC-42)
    # -------------------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        friendly_message = format_validation_error(exc)
        logger.warning("Validation failed for %s %s: %s", request.method, request.url.path, friendly_message)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "detail": friendly_message,
                "errors": jsonable_encoder(exc.errors())
            }
        )

    # -------------------------------------------------------------------------
    # 2. Database Integrity Error Handler (EC-36, EC-37)
    # -------------------------------------------------------------------------
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error("Database integrity error on %s %s: %s", request.method, request.url.path, exc)

        orig_error = getattr(exc, "orig", None)
        error_code = orig_error.args[0] if (orig_error and hasattr(orig_error, "args") and len(orig_error.args) > 0) else None

        # EC-36: Duplicate Key / Unique Constraint Violation (MySQL error 1062)
        if error_code == ER.DUP_ENTRY or "Duplicate entry" in str(exc):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Duplicate Record",
                    "detail": "This value already exists. Duplicate records are not allowed."
                }
            )

        # EC-37: Foreign Key Constraint Violation (MySQL errors 1451, 1452)
        if error_code in (ER.NO_REFERENCED_ROW, ER.NO_REFERENCED_ROW_2, ER.ROW_IS_REFERENCED, ER.ROW_IS_REFERENCED_2) or "foreign key constraint fails" in str(exc).lower():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Integrity Constraint",
                    "detail": "Referenced record not found or cannot be modified due to relational constraints."
                }
            )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Database Integrity Error",
                "detail": "The operation violated a database integrity constraint."
            }
        )

    # -------------------------------------------------------------------------
    # 3. Database Connection / Operational Error Handler (EC-34)
    # -------------------------------------------------------------------------
    @app.exception_handler(OperationalError)
    async def operational_error_handler(request: Request, exc: OperationalError):
        logger.critical("Database operational / connection failure on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Service Unavailable",
                "detail": "Database service is temporarily unavailable. Please retry shortly."
            }
        )

    # -------------------------------------------------------------------------
    # 4. Standard HTTP Exception Handler
    # -------------------------------------------------------------------------
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Pass through cleanly with uniform schema
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
                "detail": exc.detail
            },
            headers=getattr(exc, "headers", None)
        )

    # -------------------------------------------------------------------------
    # 5. Catch-All Generic Exception Handler (EC-38, safe fallback)
    # -------------------------------------------------------------------------
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            exc,
            traceback.format_exc()
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while processing your request. The transaction has been safely cancelled."
            }
        )
