"""
backend/schemas/__init__.py
=============================================================================
Export all Pydantic schemas for the PCTS application.
=============================================================================
"""

from .user import (
    UserRole,
    UserCreate,
    UserRegisterRequest,
    UserLogin,
    Token,
    UserResponse,
    UserDetailResponse
)
from .customer import CustomerCreate, CustomerUpdate, CustomerResponse
from .parcel import (
    ParcelType,
    ParcelCreate,
    ParcelStatusUpdate,
    ParcelResponse,
    calculate_shipping_charge
)

__all__ = [
    "UserRole",
    "UserCreate",
    "UserRegisterRequest",
    "UserLogin",
    "Token",
    "UserResponse",
    "UserDetailResponse",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "ParcelType",
    "ParcelCreate",
    "ParcelStatusUpdate",
    "ParcelResponse",
    "calculate_shipping_charge"
]
