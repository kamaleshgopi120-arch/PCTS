"""
backend/schemas/delivery.py — Delivery Management Schemas
=============================================================================
Validation schemas and status transition rules for parcel delivery assignments
and agent lifecycle updates.
=============================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ParcelDeliveryStatus(str, Enum):
    """
    Standard parcel delivery milestones as defined in edge_case.md Section 5.
    """
    BOOKED = "Booked"
    PICKED_UP = "Picked Up"
    IN_TRANSIT = "In Transit"
    AT_WAREHOUSE = "At Warehouse"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    FAILED_DELIVERY = "Failed Delivery"
    RETURNED = "Returned"


# Allowed state transitions (edge_case.md Section 5 - EC-23, EC-24)
VALID_STATUS_TRANSITIONS: Dict[str, List[str]] = {
    "Booked": ["Picked Up"],
    "Picked Up": ["In Transit"],
    "In Transit": ["At Warehouse"],
    "At Warehouse": ["Out for Delivery"],
    "Out for Delivery": ["Delivered", "Failed Delivery"],
    "Failed Delivery": ["Returned"],
    "Returned": [],
    "Delivered": []
}


class DeliveryPersonCreate(BaseModel):
    """Schema for registering a new delivery executive (Admin only)."""
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of delivery agent")
    phone: str = Field(..., min_length=10, max_length=15, description="Contact phone number")
    vehicle_number: Optional[str] = Field(default=None, max_length=30, description="Vehicle plate number")
    email: str = Field(..., max_length=100, description="Login email address")
    password: Optional[str] = Field(default="Delivery@12345", min_length=6, description="Initial account password")


class DeliveryCreate(BaseModel):
    """Schema for assigning a parcel to a delivery person (EC-26, EC-27, EC-28, EC-29)."""
    parcel_id: int = Field(..., gt=0, description="ID of parcel to assign")
    delivery_person_id: int = Field(..., gt=0, description="ID of active delivery person")


class DeliveryStatusUpdate(BaseModel):
    """Schema for updating parcel status and location by delivery person or admin."""
    status: str = Field(..., min_length=2, max_length=30, description="Target status name")
    location: str = Field(..., min_length=2, max_length=100, description="Current checkpoint/hub location")
    notes: Optional[str] = Field(default=None, max_length=255, description="Optional delivery remarks")

    @field_validator("status")
    @classmethod
    def validate_status_exists(cls, v: str) -> str:
        cleaned = v.strip()
        status_map = {s.value.lower(): s.value for s in ParcelDeliveryStatus}
        if cleaned.lower() not in status_map:
            raise ValueError("Invalid status value.")
        return status_map[cleaned.lower()]

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Location must contain at least two non-whitespace characters.")
        return cleaned


class DeliveryPersonResponse(BaseModel):
    """Profile schema for delivery agents."""
    delivery_person_id: int = Field(..., description="Unique agent ID")
    user_id: int = Field(..., description="Foreign key to user account")
    full_name: str = Field(..., description="Agent's full name")
    phone: str = Field(..., description="Agent's phone number")
    vehicle_number: Optional[str] = Field(default=None, description="Vehicle registration plate")
    is_active: bool = Field(default=True, description="Active status")

    model_config = ConfigDict(from_attributes=True)


class DeliveryResponse(BaseModel):
    """Full details of a delivery assignment."""
    delivery_id: int = Field(..., description="Assignment record primary key")
    parcel_id: int = Field(..., description="Assigned parcel primary key")
    tracking_id: str = Field(..., description="Public tracking ID")
    delivery_person_id: int = Field(..., description="Assigned agent ID")
    delivery_person_name: str = Field(..., description="Name of assigned agent")
    delivery_person_phone: str = Field(..., description="Phone number of agent")
    assigned_at: datetime = Field(..., description="Timestamp when assigned")
    delivered_at: Optional[datetime] = Field(default=None, description="Delivery completion timestamp")
    status: str = Field(..., description="Current parcel delivery status")
    location: Optional[str] = Field(default=None, description="Current parcel location")
    receiver_name: str = Field(..., description="Receiver name")
    receiver_phone: str = Field(..., description="Receiver contact")
    receiver_address: Optional[str] = Field(default=None, description="Street address for delivery")
    destination_city: str = Field(..., description="Destination city")
    weight_kg: float = Field(..., description="Parcel weight in kg")
    payment_status: Optional[str] = Field(default="Pending", description="Payment status (Pending, Paid)")
    payment_method: Optional[str] = Field(default="Cash on Delivery", description="Payment method")
    payment_amount: Optional[float] = Field(default=None, description="Amount due / collected in Rs.")

    model_config = ConfigDict(from_attributes=True)
