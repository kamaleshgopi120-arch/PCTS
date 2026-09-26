"""
backend/schemas/parcel.py
=============================================================================
Parcel Booking, Tracking, and Charge Calculation Validation Schemas
=============================================================================
"""

import re
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class ParcelType(str, Enum):
    """Allowed parcel categories."""
    DOCUMENT = "Document"
    ELECTRONICS = "Electronics"
    FRAGILE = "Fragile"
    CLOTHING = "Clothing"
    GENERAL = "General"


def calculate_shipping_charge(weight_kg: float) -> float:
    """
    Implements the official PCTS pricing rules (from databaseDesign.md Section 5):
      - 0.01 - 1.00 kg:   Rs. 50 flat
      - 1.01 - 5.00 kg:   Rs. 30 per kg
      - 5.01 - 20.00 kg:  Rs. 20 per kg
      - Above 20.00 kg:   Rs. 15 per kg
    """
    if weight_kg <= 0:
        return 0.00
    elif weight_kg <= 1.00:
        return 50.00
    elif weight_kg <= 5.00:
        return round(weight_kg * 30.00, 2)
    elif weight_kg <= 20.00:
        return round(weight_kg * 20.00, 2)
    else:
        return round(weight_kg * 15.00, 2)


class ParcelBase(BaseModel):
    """Shared core parcel fields."""
    sender_name: str = Field(..., min_length=2, max_length=100, description="Sender's full name")
    sender_phone: str = Field(..., min_length=10, max_length=15, description="Sender's phone number")
    receiver_name: str = Field(..., min_length=2, max_length=100, description="Receiver's full name")
    receiver_phone: str = Field(..., min_length=10, max_length=15, description="Receiver's phone number")
    source_city: str = Field(..., min_length=2, max_length=50, description="Pickup origin city")
    destination_city: str = Field(..., min_length=2, max_length=50, description="Delivery destination city")
    parcel_type: ParcelType = Field(default=ParcelType.GENERAL, description="Category of parcel")
    weight_kg: float = Field(
        ...,
        gt=0.0,
        le=500.0,
        description="Parcel weight in kilograms (must be greater than 0 and up to 500 kg)"
    )
    description: Optional[str] = Field(default=None, max_length=500, description="Contents description")

    @field_validator("sender_phone", "receiver_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip()
        if not re.fullmatch(r"^\+?[0-9]{10,14}$", cleaned):
            raise ValueError("Phone number must contain between 10 and 14 digits and no letters.")
        return cleaned

    @model_validator(mode="after")
    def validate_different_cities(self) -> "ParcelBase":
        """
        Enforces EC-15 from edge_case.md:
        Source and destination cities cannot be the same.
        """
        src = self.source_city.strip().lower()
        dst = self.destination_city.strip().lower()
        if src == dst:
            raise ValueError("Source and destination cities cannot be the same.")
        return self


class ParcelCreate(ParcelBase):
    """
    Schema for booking a new parcel shipment.
    `customer_id` is optional in the payload because it is automatically resolved
    from the logged-in customer's JWT token (or provided explicitly by admins).
    """
    customer_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Customer ID (inferred from JWT token for customers; required for admins)"
    )


class ParcelStatusUpdate(BaseModel):
    """Schema for updating the status and current location of a parcel."""
    status: str = Field(..., min_length=2, max_length=30, description="e.g., In Transit, Out for Delivery, Delivered")
    location: str = Field(..., min_length=2, max_length=100, description="Physical hub/city location")


class ParcelResponse(ParcelBase):
    """Schema for returning full parcel details to client."""
    parcel_id: int = Field(..., description="Internal primary key")
    tracking_id: str = Field(..., description="Unique human-readable tracking code")
    customer_id: int = Field(..., description="Booking customer ID")
    charge: float = Field(..., description="Calculated delivery charge in Rs.")
    booked_at: datetime = Field(..., description="Timestamp when booking was confirmed")
    status: Optional[str] = Field(default="Booked", description="Current delivery status")
    location: Optional[str] = Field(default=None, description="Current physical location")
    payment_status: Optional[str] = Field(default="Pending", description="Payment settlement status")
    payment_amount: Optional[float] = Field(default=None, description="Total amount due / paid")

    model_config = ConfigDict(from_attributes=True)


class TrackingResponse(BaseModel):
    """Public tracking response schema."""
    tracking_id: str = Field(..., description="Unique Tracking ID")
    status: str = Field(..., description="Current status (e.g. Booked, In Transit, Delivered)")
    location: Optional[str] = Field(None, description="Latest known hub/location")
    source_city: str = Field(..., description="Origin city")
    destination_city: str = Field(..., description="Destination city")
    receiver_name: str = Field(..., description="Receiver name")
    weight_kg: float = Field(..., description="Weight in kg")
    booked_at: datetime = Field(..., description="Booking timestamp")
    last_updated: datetime = Field(..., description="Timestamp of last status change")
    is_delivered: bool = Field(default=False, description="True if parcel has been delivered")
    delivered_at: Optional[datetime] = Field(default=None, description="Delivery completion timestamp")

    model_config = ConfigDict(from_attributes=True)
