"""
backend/schemas/report.py — Reports & Analytics Validation Schemas
=============================================================================
Pydantic schemas for executive summary, status aggregation, and delivery metrics.
=============================================================================
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ParcelStatusSummary(BaseModel):
    """Metrics for a single parcel status bucket."""
    status: str = Field(..., description="Parcel status (Booked, In Transit, etc.)")
    count: int = Field(..., description="Number of parcels in this status")
    percentage: float = Field(..., description="Percentage of total parcels")
    total_charges: float = Field(..., description="Sum of delivery charges in Rs.")
    total_weight_kg: float = Field(..., description="Sum of weight in kg")


class ParcelReportResponse(BaseModel):
    """Aggregated report of all parcels in the system."""
    total_parcels: int = Field(..., description="Total parcels recorded")
    total_revenue: float = Field(..., description="Total shipment revenue booked")
    average_weight_kg: float = Field(..., description="Average parcel weight")
    by_status: List[ParcelStatusSummary] = Field(default_factory=list)


class PaymentStatusSummary(BaseModel):
    """Metrics for a single payment status bucket."""
    payment_status: str = Field(..., description="Status (Pending, Paid, Failed)")
    count: int = Field(..., description="Number of payments in this status")
    total_amount: float = Field(..., description="Total monetary amount in Rs.")
    percentage: float = Field(..., description="Percentage of total payment count")


class PaymentReportResponse(BaseModel):
    """Aggregated financial report of payments."""
    total_payments: int = Field(..., description="Total payment records")
    total_amount: float = Field(..., description="Gross payment amount due / collected")
    collected_amount: float = Field(..., description="Amount successfully collected ('Paid')")
    pending_amount: float = Field(..., description="Amount pending settlement")
    by_status: List[PaymentStatusSummary] = Field(default_factory=list)
    by_method: Dict[str, float] = Field(default_factory=dict, description="Revenue by payment method")


class DeliveryAgentWorkload(BaseModel):
    """Performance and workload summary for a delivery agent."""
    delivery_person_id: int = Field(..., description="Delivery person ID")
    full_name: str = Field(..., description="Agent name")
    phone: str = Field(..., description="Agent contact")
    vehicle_number: Optional[str] = Field(default=None)
    assigned_count: int = Field(..., description="Total parcels assigned")
    delivered_count: int = Field(..., description="Total parcels delivered")
    pending_count: int = Field(..., description="Parcels currently in progress")
    completion_rate: float = Field(..., description="Percentage of assigned deliveries completed")


class DeliveryReportResponse(BaseModel):
    """Aggregated delivery performance metrics."""
    total_deliveries: int = Field(..., description="Total assignments across system")
    total_delivered: int = Field(..., description="Total completed deliveries")
    overall_completion_rate: float = Field(..., description="Overall completion percentage")
    agents: List[DeliveryAgentWorkload] = Field(default_factory=list)


class MonthlyReportResponse(BaseModel):
    """Executive monthly summary generated via MySQL Stored Procedure."""
    year: int
    month: int
    total_parcels_booked: int
    total_revenue: float
    average_weight_kg: float
    by_status: List[Dict[str, Any]] = Field(default_factory=list)
    by_destination: List[Dict[str, Any]] = Field(default_factory=list)
