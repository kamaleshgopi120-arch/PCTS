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
    "Booked": ["Picked Up", "In Transit", "At Warehouse", "Out for Delivery", "Delivered"],
    "Picked Up": ["In Transit", "At Warehouse", "Out for Delivery", "Delivered"],
    "In Transit": ["At Warehouse", "Out for Delivery", "Delivered", "Failed Delivery"],
    "At Warehouse": ["In Transit", "Out for Delivery", "Delivered"],
    "Out for Delivery": ["Delivered", "Failed Delivery"],
    "Failed Delivery": ["At Warehouse", "Out for Delivery", "Returned"],
    "Returned": [],
    "Delivered": []  # Terminal state: EC-23 cannot update status of delivered parcel
}


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
    destination_city: str = Field(..., description="Destination city")
    weight_kg: float = Field(..., description="Parcel weight in kg")

    model_config = ConfigDict(from_attributes=True)
