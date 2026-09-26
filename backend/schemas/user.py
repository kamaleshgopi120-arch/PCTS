"""
backend/schemas/user.py
=============================================================================
User Authentication and Profile Validation Schemas (Pydantic v2)
=============================================================================
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserRole(str, Enum):
    """Allowed user roles matching the MySQL ENUM definition."""
    CUSTOMER = "customer"
    ADMIN = "admin"
    DELIVERY = "delivery"


class UserBase(BaseModel):
    """Shared fields for User models."""
    email: EmailStr = Field(..., description="Valid login email address (e.g., user@example.com)")
    role: UserRole = Field(default=UserRole.CUSTOMER, description="User role in the system")


class UserCreate(UserBase):
    """
    Schema for user registration.
    Enforces password rules (EC-06 from edge_case.md).
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Password must be between 8 and 64 characters long"
    )

    @field_validator("password")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Password cannot be blank or contain only spaces.")
        return v


class UserLogin(BaseModel):
    """Schema for user authentication request."""
    email: EmailStr = Field(..., description="Registered login email")
    password: str = Field(..., min_length=1, description="Account password")


class UserResponse(UserBase):
    """
    Schema for returning user information to clients.
    NOTE: password_hash is strictly EXCLUDED for security.
    """
    user_id: int = Field(..., description="Unique user identifier")
    created_at: datetime = Field(..., description="Timestamp when account was created")

    model_config = ConfigDict(from_attributes=True)
