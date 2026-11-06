"""
backend/schemas/customer.py
=============================================================================
Customer Profile Validation Schemas (Pydantic v2)
=============================================================================
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CustomerBase(BaseModel):
    """Shared fields for customer profile."""
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full legal name of the customer"
    )
    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Contact phone number (10-15 digits)"
    )
    address: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Street address or residence details"
    )
    city: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="City of residence"
    )

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Customer name must be at least 2 characters long.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone_digits(cls, v: str) -> str:
        """
        Enforces EC-10 from edge_case.md:
        Phone number must contain only digits (allowing optional leading +).
        """
        cleaned = v.strip()
        # Allow optional leading '+' followed by 10-14 digits
        if not re.fullmatch(r"^\+?[0-9]{10,14}$", cleaned):
            raise ValueError("Phone number must contain between 10 and 14 digits and no letters.")
        return cleaned


class CustomerCreate(CustomerBase):
    """Schema for creating a customer record linked to a User account."""
    user_id: int = Field(..., gt=0, description="Foreign key reference to existing User ID")


class CustomerUpdate(BaseModel):
    """Schema for updating customer profile details."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=2, max_length=50)

    @field_validator("full_name", "city")
    @classmethod
    def clean_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if len(cleaned) < 2:
                raise ValueError("Value must contain at least two non-whitespace characters.")
            return cleaned
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not re.fullmatch(r"^\+?[0-9]{10,14}$", cleaned):
                raise ValueError("Phone number must contain between 10 and 14 digits and no letters.")
            return cleaned
        return v


class CustomerResponse(CustomerBase):
    """Schema for returning customer profile to client."""
    customer_id: int = Field(..., description="Unique customer identifier")
    user_id: int = Field(..., description="Associated user ID")
    email: Optional[str] = Field(default=None, description="Linked user account email")

    model_config = ConfigDict(from_attributes=True)
