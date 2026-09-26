"""
backend/routers/tracking.py
=============================================================================
Public Parcel Tracking API Endpoints
=============================================================================

This router handles public tracking lookups. Customers and recipients can track
their packages in real-time by Tracking ID without requiring an account or login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models.parcel import Parcel
from backend.schemas.parcel import TrackingResponse, TrackingHistoryEvent
from backend.mongo import get_tracking_history

router = APIRouter(prefix="/api/track", tags=["Public Tracking"])


@router.get(
    "/{tracking_id}",
    response_model=TrackingResponse,
    summary="Track a parcel in real-time by Tracking ID (Public Endpoint)"
)
def track_parcel_public(
    tracking_id: str,
    db: Session = Depends(get_db)
):
    """
    Public tracking endpoint:
    - No login required.
    - Enforces EC-18: Checks for empty Tracking ID.
    - Enforces EC-20: Strips whitespace and normalizes tracking code to uppercase.
    - Enforces EC-19: Returns 404 Not Found if tracking ID is not found.
    - Retrieves real-time status and delivery location from MySQL.
    - Retrieves complete chronological milestone history from MongoDB.
    - Enforces EC-21: If MongoDB is unavailable or fails, returns the current status
      from MySQL along with warning: "Tracking history is temporarily unavailable."
    """
    # EC-18: Check for empty tracking ID
    if not tracking_id or tracking_id.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a Tracking ID."
        )

    # EC-20: Normalize tracking ID (strip spaces, uppercase)
    cleaned_id = tracking_id.strip().upper()

    # EC-19: Query parcel in database
    parcel = db.scalar(select(Parcel).where(Parcel.tracking_id == cleaned_id))
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No parcel found with this Tracking ID."
        )

    current_status = parcel.status.status if parcel.status else "Booked"
    current_location = parcel.status.location if parcel.status else f"{parcel.source_city} Booking Office"
    last_updated = parcel.status.updated_at if (parcel.status and parcel.status.updated_at) else parcel.booked_at
    is_delivered = current_status.strip().lower() == "delivered"
    delivered_at = parcel.delivery.delivered_at if (parcel.delivery and is_delivered) else None

    # Retrieve history from MongoDB (Fault tolerant with EC-21 / EC-35)
    history_events = get_tracking_history(cleaned_id)
    if history_events is None:
        warning_msg = "Tracking history is temporarily unavailable."
        formatted_history = []
    else:
        warning_msg = None
        formatted_history = [
            TrackingHistoryEvent(
                event_id=ev.get("event_id"),
                status=ev["status"],
                location=ev["location"],
                updated_by=ev["updated_by"],
                timestamp=ev["timestamp"],
                notes=ev.get("notes")
            )
            for ev in history_events
        ]

    return TrackingResponse(
        tracking_id=parcel.tracking_id,
        status=current_status,
        location=current_location,
        source_city=parcel.source_city,
        destination_city=parcel.destination_city,
        receiver_name=parcel.receiver_name,
        weight_kg=float(parcel.weight_kg),
        booked_at=parcel.booked_at,
        last_updated=last_updated,
        is_delivered=is_delivered,
        delivered_at=delivered_at,
        history=formatted_history,
        warning=warning_msg
    )
