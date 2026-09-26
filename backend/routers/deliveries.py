"""
backend/routers/deliveries.py — Delivery Management API Endpoints
=============================================================================
This router handles parcel delivery assignments, delivery agent work queues,
and parcel milestone status transitions.

Enforces Edge Cases from edge_case.md:
- EC-22: Invalid status value.
- EC-23: Cannot update status of a delivered parcel.
- EC-24: Invalid status transition (cannot move backward or skip illegal states).
- EC-25: A delivery person can only update parcels assigned to them (403 Forbidden).
- EC-26: A parcel cannot be assigned more than once (400 Bad Request).
- EC-27: Cannot assign a parcel that has already been delivered (400 Bad Request).
- EC-28: Delivery person must exist and have is_active == True.
- EC-29: Assigned parcel must exist (404 Not Found).
=============================================================================
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models.user import User
from backend.models.parcel import Parcel
from backend.models.parcel_status import ParcelStatus
from backend.models.delivery import Delivery
from backend.models.delivery_person import DeliveryPerson
from backend.mongo import log_tracking_event
from backend.security import (
    get_current_user,
    require_admin,
    require_delivery,
    require_staff
)
from backend.schemas.delivery import (
    DeliveryCreate,
    DeliveryStatusUpdate,
    DeliveryPersonResponse,
    DeliveryResponse,
    VALID_STATUS_TRANSITIONS
)

router = APIRouter(prefix="/api/deliveries", tags=["Delivery Management"])


def build_delivery_response(d: Delivery) -> DeliveryResponse:
    """Helper to convert a Delivery ORM model into DeliveryResponse."""
    parcel = d.parcel
    agent = d.delivery_person
    cur_status = parcel.status.status if parcel and parcel.status else "Booked"
    cur_loc = parcel.status.location if parcel and parcel.status else None

    return DeliveryResponse(
        delivery_id=d.delivery_id,
        parcel_id=d.parcel_id,
        tracking_id=parcel.tracking_id if parcel else "",
        delivery_person_id=d.delivery_person_id,
        delivery_person_name=agent.full_name if agent else "Unknown",
        delivery_person_phone=agent.phone if agent else "Unknown",
        assigned_at=d.assigned_at,
        delivered_at=d.delivered_at,
        status=cur_status,
        location=cur_loc,
        receiver_name=parcel.receiver_name if parcel else "",
        receiver_phone=parcel.receiver_phone if parcel else "",
        destination_city=parcel.destination_city if parcel else "",
        weight_kg=float(parcel.weight_kg) if parcel else 0.0,
    )


# -----------------------------------------------------------------------------
# 1. LIST DELIVERY AGENTS (Staff / Admin View)
# -----------------------------------------------------------------------------
@router.get(
    "/agents",
    response_model=List[DeliveryPersonResponse],
    summary="List all delivery staff agents (Admin/Staff only)",
    dependencies=[Depends(require_staff)]
)
def list_delivery_agents(
    active_only: bool = Query(True, description="Filter for active staff only"),
    db: Session = Depends(get_db)
):
    """Returns active delivery staff profiles for dispatch and assignment."""
    query = select(DeliveryPerson)
    if active_only:
        query = query.where(DeliveryPerson.is_active.is_(True))
    agents = db.scalars(query).all()
    return agents


# -----------------------------------------------------------------------------
# 2. VIEW ASSIGNED DELIVERIES FOR LOGGED-IN AGENT (GET /api/deliveries/my)
# -----------------------------------------------------------------------------
@router.get(
    "/my",
    response_model=List[DeliveryResponse],
    summary="View assigned deliveries for the current delivery agent"
)
def get_my_deliveries(
    completed: Optional[bool] = Query(None, description="Filter completed vs pending deliveries"),
    current_user: User = Depends(require_delivery),
    db: Session = Depends(get_db)
):
    """
    Delivery agent views their current queue of assigned parcels.
    - Requires role 'delivery'.
    - Can filter by pending vs completed shipments.
    """
    if not current_user.delivery_person:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not linked to a delivery agent profile."
        )

    agent_id = current_user.delivery_person.delivery_person_id
    query = (
        select(Delivery)
        .where(Delivery.delivery_person_id == agent_id)
        .order_by(Delivery.assigned_at.desc())
    )

    if completed is True:
        query = query.where(Delivery.delivered_at.isnot(None))
    elif completed is False:
        query = query.where(Delivery.delivered_at.is_(None))

    deliveries = db.scalars(query).all()
    return [build_delivery_response(d) for d in deliveries]


# -----------------------------------------------------------------------------
# 3. ASSIGN PARCEL TO DELIVERY PERSON (POST /api/deliveries)
# -----------------------------------------------------------------------------
@router.post(
    "",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a parcel to a delivery person (Admin only)"
)
def assign_delivery(
    payload: DeliveryCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Assigns a parcel to a delivery person with strict edge-case validation:
    - EC-29: Parcel must exist (404 Not Found).
    - EC-28: Delivery person must exist and be active (400 Bad Request).
    - EC-27: Cannot assign a parcel that is already delivered (400 Bad Request).
    - EC-26: Parcel cannot be assigned to more than one agent (400 Bad Request).
    - Records assignment in MySQL and logs milestone in MongoDB.
    """
    # EC-29: Verify parcel exists
    parcel = db.scalar(select(Parcel).where(Parcel.parcel_id == payload.parcel_id))
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found."
        )

    # EC-27: Check if parcel is already delivered
    current_status = parcel.status.status if parcel.status else "Booked"
    if current_status.strip().title() == "Delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign a delivered parcel."
        )

    # EC-26: Check if parcel already has an active delivery assignment
    existing_delivery = db.scalar(select(Delivery).where(Delivery.parcel_id == payload.parcel_id))
    if existing_delivery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This parcel is already assigned to a delivery person."
        )

    # EC-28: Verify delivery person exists and is active
    agent = db.scalar(select(DeliveryPerson).where(DeliveryPerson.delivery_person_id == payload.delivery_person_id))
    if not agent or not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery person not found or inactive."
        )

    # Create delivery assignment
    new_delivery = Delivery(
        parcel_id=payload.parcel_id,
        delivery_person_id=payload.delivery_person_id,
        assigned_at=datetime.now()
    )
    db.add(new_delivery)

    # Transition parcel status to 'Picked Up' if still 'Booked'
    if current_status == "Booked":
        if not parcel.status:
            parcel.status = ParcelStatus(
                parcel_id=parcel.parcel_id,
                status="Picked Up",
                location=f"Assigned to {agent.full_name}",
                updated_at=datetime.now()
            )
            db.add(parcel.status)
        else:
            parcel.status.status = "Picked Up"
            parcel.status.location = f"Assigned to {agent.full_name}"
            parcel.status.updated_at = datetime.now()

    db.commit()
    db.refresh(new_delivery)

    # Log milestone into MongoDB tracking history
    log_tracking_event(
        tracking_id=parcel.tracking_id,
        status="Picked Up" if current_status == "Booked" else current_status,
        location=f"Assigned to {agent.full_name} ({agent.vehicle_number or 'Vehicle'})",
        updated_by=current_user.email,
        notes=f"Delivery assigned to {agent.full_name} (Phone: {agent.phone})"
    )

    return build_delivery_response(new_delivery)


# -----------------------------------------------------------------------------
# 4. LIST ALL DELIVERIES (Admin View)
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[DeliveryResponse],
    summary="List all deliveries with filters and pagination (Admin only)",
    dependencies=[Depends(require_admin)]
)
def list_all_deliveries(
    delivery_person_id: Optional[int] = Query(None, description="Filter by agent ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by parcel status"),
    completed: Optional[bool] = Query(None, description="Filter completed vs active deliveries"),
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(20, ge=1, le=100, description="Limit"),
    db: Session = Depends(get_db)
):
    """Lists all deliveries across the entire logistics network."""
    query = select(Delivery).order_by(Delivery.delivery_id.desc())

    if delivery_person_id:
        query = query.where(Delivery.delivery_person_id == delivery_person_id)

    if completed is True:
        query = query.where(Delivery.delivered_at.isnot(None))
    elif completed is False:
        query = query.where(Delivery.delivered_at.is_(None))

    deliveries = db.scalars(query.offset(skip).limit(limit)).all()
    return [build_delivery_response(d) for d in deliveries]


# -----------------------------------------------------------------------------
# 5. GET SINGLE DELIVERY DETAILS
# -----------------------------------------------------------------------------
@router.get(
    "/{delivery_id}",
    response_model=DeliveryResponse,
    summary="Get delivery details by ID"
)
def get_delivery_by_id(
    delivery_id: int,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """
    Get delivery assignment details:
    - Delivery agents can only view their own assignments.
    - Admins can view any assignment.
    """
    delivery = db.scalar(select(Delivery).where(Delivery.delivery_id == delivery_id))
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery assignment not found."
        )

    # Permission check for delivery agents
    if current_user.role == "delivery":
        if (
            not current_user.delivery_person
            or delivery.delivery_person_id != current_user.delivery_person.delivery_person_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this parcel."
            )

    return build_delivery_response(delivery)


# -----------------------------------------------------------------------------
# 6. UPDATE DELIVERY STATUS (PUT /api/deliveries/{id}/status)
# -----------------------------------------------------------------------------
@router.put(
    "/{delivery_id}/status",
    response_model=DeliveryResponse,
    summary="Update delivery status and milestone location"
)
def update_delivery_status(
    delivery_id: int,
    status_update: DeliveryStatusUpdate,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """
    Updates parcel status along its delivery route:
    - EC-25: A delivery person can only update parcels assigned to them.
    - EC-22: Status value must be a valid allowed milestone.
    - EC-23: Cannot update status of an already delivered parcel.
    - EC-24: Enforces valid state transition hierarchy (cannot move backward).
    - When marked 'Delivered', sets delivery.delivered_at timestamp.
    - MySQL trigger `trg_after_status_update` logs into `parcel_status_audit`.
    - MongoDB logs milestone into `tracking_history`.
    """
    delivery = db.scalar(select(Delivery).where(Delivery.delivery_id == delivery_id))
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery assignment not found."
        )

    # EC-25: Agent ownership validation
    if current_user.role == "delivery":
        if (
            not current_user.delivery_person
            or delivery.delivery_person_id != current_user.delivery_person.delivery_person_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this parcel."
            )

    parcel = delivery.parcel
    current_status = parcel.status.status if parcel and parcel.status else "Booked"
    target_status = status_update.status

    # EC-23: Cannot update a parcel that is already delivered
    if current_status.strip().lower() == "delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update status of a delivered parcel."
        )

    # EC-24: Check valid status transition hierarchy
    allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])
    if target_status not in allowed_transitions and target_status != current_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{current_status}' to '{target_status}'."
        )

    # Update parcel_status in MySQL
    if not parcel.status:
        parcel.status = ParcelStatus(
            parcel_id=parcel.parcel_id,
            status=target_status,
            location=status_update.location,
            updated_at=datetime.now()
        )
        db.add(parcel.status)
    else:
        parcel.status.status = target_status
        parcel.status.location = status_update.location
        parcel.status.updated_at = datetime.now()

    # If delivered, record delivery completion timestamp
    if target_status == "Delivered":
        delivery.delivered_at = datetime.now()

    db.commit()
    db.refresh(delivery)

    # Log milestone into MongoDB tracking history
    log_tracking_event(
        tracking_id=parcel.tracking_id,
        status=target_status,
        location=status_update.location,
        updated_by=current_user.email,
        notes=status_update.notes
    )

    return build_delivery_response(delivery)
