"""
backend/schemas/user.py
=============================================================================
User Authentication and Profile Validation Schemas (Pydantic v2)
=============================================================================
"""

import re
from datetime import datetime
from enum import Enum
from typing import Optional
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


class UserRegisterRequest(BaseModel):
    """
    Comprehensive registration schema that creates both the login account (`user`)
    and the associated profile (`customer` or `delivery_person`) in a single transaction.
    
    SECURITY FIX: Admin role self-registration is blocked - admin accounts must be 
    created manually or by existing administrators.
    """
    email: EmailStr = Field(..., description="Login email address")
    password: str = Field(..., min_length=8, max_length=64, description="Password (at least 8 chars)")
    role: UserRole = Field(default=UserRole.CUSTOMER, description="Account role")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    phone: str = Field(..., min_length=10, max_length=15, description="10-14 digit phone number")
    address: Optional[str] = Field(default=None, max_length=255, description="Residential address")
    city: Optional[str] = Field(default=None, max_length=50, description="City")
    vehicle_number: Optional[str] = Field(default=None, max_length=20, description="Vehicle number (for delivery staff)")

    @field_validator("password")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Password cannot be blank or contain only spaces.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip()
        if not re.fullmatch(r"^\+?[0-9]{10,14}$", cleaned):
            raise ValueError("Phone number must contain between 10 and 14 digits and no letters.")
        return cleaned

    @field_validator("role")
    @classmethod
    def validate_role_not_admin(cls, v: UserRole) -> UserRole:
        """
        SECURITY FIX (EC-ADMIN-SELF-REG): Prevent users from self-registering 
        as administrators through the public registration endpoint.
        """
        if v == UserRole.ADMIN:
            raise ValueError("Admin accounts cannot be self-registered. Please contact system administrator.")
        return v


class UserLogin(BaseModel):
    """Schema for user authentication request."""
    email: EmailStr = Field(..., description="Registered login email")
    password: str = Field(..., min_length=1, description="Account password")


class Token(BaseModel):
    """Schema for JWT Token response returned upon successful login."""
    access_token: str = Field(..., description="JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token type")
    role: str = Field(..., description="Role of the authenticated user")
    user_id: int = Field(..., description="Unique User ID")
    email: str = Field(..., description="User email")


class UserResponse(UserBase):
    """
    Schema for returning user information to clients.
    NOTE: password_hash is strictly EXCLUDED for security.
    """
    user_id: int = Field(..., description="Unique user identifier")
    created_at: datetime = Field(..., description="Timestamp when account was created")

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserResponse):
    """Extended user response including associated profile details."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    vehicle_number: Optional[str] = None
