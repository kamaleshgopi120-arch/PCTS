"""
backend/schemas/payment.py — Payment Validation & Response Schemas
=============================================================================
Validation schemas and business rules for payment processing, settlement,
and payment history queries.
=============================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PaymentStatus(str, Enum):
    """Allowed payment settlement states matching database enum."""
    PENDING = "Pending"
    PAID = "Paid"
    FAILED = "Failed"


class PaymentUpdate(BaseModel):
    """
    Schema for settling or updating payment status (PUT /api/payments/{id}).
    Enforces EC-31: Amount must be greater than 0 if provided.
    """
    payment_status: PaymentStatus = Field(..., description="Target status: Pending, Paid, or Failed")
    payment_method: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=30,
        description="e.g. Cash, Card, UPI, Online, Cash on Delivery"
    )
    amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Payment amount in Rs. (must be strictly > 0, EC-31)"
    )

    @field_validator("payment_method")
    @classmethod
    def clean_method(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().title()
        return v


class PaymentCreate(BaseModel):
    """Schema for initializing or recording a payment for a parcel."""
    parcel_id: int = Field(..., gt=0, description="Parcel foreign key ID")
    amount: float = Field(..., gt=0, description="Payment amount (EC-31)")
    payment_method: Optional[str] = Field(default="Cash on Delivery", max_length=30)
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)


class PaymentResponse(BaseModel):
    """Schema for returning payment details to client."""
    payment_id: int = Field(..., description="Primary key")
    parcel_id: int = Field(..., description="Associated parcel ID")
    tracking_id: str = Field(..., description="Associated tracking ID")
    amount: float = Field(..., description="Total charge amount in Rs.")
    payment_method: Optional[str] = Field(default=None, description="Payment method used")
    payment_status: str = Field(..., description="Status (Pending, Paid, Failed)")
    paid_at: Optional[datetime] = Field(default=None, description="Settlement timestamp")
    customer_name: Optional[str] = Field(default=None, description="Booking customer name")
    receiver_name: Optional[str] = Field(default=None, description="Receiver name")

    model_config = ConfigDict(from_attributes=True)
