"""
backend/routers/parcels.py
=============================================================================
Parcel Booking, Management, and Charge Calculation API Endpoints
=============================================================================
"""

import random
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from backend.database import get_db
from backend.models.user import User
from backend.models.customer import Customer
from backend.models.parcel import Parcel
from backend.models.parcel_status import ParcelStatus
from backend.models.delivery import Delivery
from backend.models.payment import Payment
from backend.schemas.parcel import (
    ParcelCreate,
    ParcelStatusUpdate,
    ParcelResponse,
    calculate_shipping_charge
)
from backend.schemas.delivery import ParcelDeliveryStatus, VALID_STATUS_TRANSITIONS
from backend.security import get_current_user, require_staff
from backend.mongo import log_tracking_event

router = APIRouter(prefix="/api/parcels", tags=["Parcel Booking & Management"])


def ensure_delivery_agent_owns_parcel(
    parcel_id: int,
    current_user: User,
    db: Session
) -> None:
    if current_user.role != "delivery":
        return

    delivery_person = current_user.delivery_person
    assignment = db.scalar(select(Delivery).where(Delivery.parcel_id == parcel_id))
    if (
        not delivery_person
        or not assignment
        or assignment.delivery_person_id != delivery_person.delivery_person_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this parcel."
        )


# -----------------------------------------------------------------------------
# HELPER: Generate Unique Tracking ID (Collision Resistant - EC-16)
# -----------------------------------------------------------------------------
def generate_unique_tracking_id(db: Session, max_retries: int = 5) -> str:
    """
    Generates a unique Tracking ID: PCTS-YYYYMMDD-XXXX.
    Enforces EC-16: Retries with a new random number if a collision occurs.
    """
    date_str = datetime.now().strftime("%Y%m%d")
    for _ in range(max_retries):
        random_suffix = f"{random.randint(1000, 9999)}"
        candidate_id = f"PCTS-{date_str}-{random_suffix}"

        # Check collision in DB
        exists = db.scalar(select(Parcel.parcel_id).where(Parcel.tracking_id == candidate_id))
        if not exists:
            return candidate_id

    existing_ids = set(db.scalars(
        select(Parcel.tracking_id).where(Parcel.tracking_id.like(f"PCTS-{date_str}-%"))
    ).all())
    for suffix in range(1000, 10000):
        candidate_id = f"PCTS-{date_str}-{suffix:04d}"
        if candidate_id not in existing_ids:
            return candidate_id

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Unable to generate a unique tracking ID. Please try again."
    )


# -----------------------------------------------------------------------------
# HELPER: Build ParcelResponse with Status and Payment Details
# -----------------------------------------------------------------------------
def build_parcel_response(parcel: Parcel) -> ParcelResponse:
    delivery = parcel.delivery
    agent = delivery.delivery_person if delivery else None
    payment = parcel.payment

    return ParcelResponse(
        parcel_id=parcel.parcel_id,
        tracking_id=parcel.tracking_id,
        customer_id=parcel.customer_id,
        sender_name=parcel.sender_name,
        sender_phone=parcel.sender_phone,
        receiver_name=parcel.receiver_name,
        receiver_phone=parcel.receiver_phone,
        receiver_address=parcel.receiver_address,
        source_city=parcel.source_city,
        destination_city=parcel.destination_city,
        parcel_type=parcel.parcel_type,
        weight_kg=float(parcel.weight_kg),
        description=parcel.description,
        charge=float(parcel.charge),
        booked_at=parcel.booked_at,
        status=parcel.status.status if parcel.status else "Booked",
        location=parcel.status.location if parcel.status else None,
        payment_status=payment.payment_status if payment else "Pending",
        payment_method=payment.payment_method if payment else "Cash on Delivery",
        payment_amount=float(payment.amount) if payment else float(parcel.charge),
        is_assigned=bool(delivery),
        delivery_person_id=delivery.delivery_person_id if delivery else None,
        delivery_person_name=agent.full_name if agent else None,
        delivery_person_phone=agent.phone if agent else None,
        delivery_id=delivery.delivery_id if delivery else None
    )


# -----------------------------------------------------------------------------
# 1. BOOK A NEW PARCEL (Customer or Admin)
# -----------------------------------------------------------------------------
@router.post(
    "",
    response_model=ParcelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a new parcel shipment"
)
def book_parcel(
    parcel_in: ParcelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Books a new parcel shipment with atomic transaction:
    - Resolves customer_id (from JWT token for customers; explicitly provided for admins).
    - Enforces EC-17: Validates customer exists.
    - Calculates shipping charge using official weight tiers.
    - Generates unique Tracking ID (PCTS-YYYYMMDD-XXXX) with collision checks (EC-16).
    - Inserts into `parcel`, initial `parcel_status` ('Booked'), and `payment` ('Pending').
    """
    # 1. Determine customer_id
    if current_user.role == "customer":
        if not current_user.customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer profile not found for this account."
            )
        target_customer_id = current_user.customer.customer_id
    elif current_user.role == "admin":
        if not parcel_in.customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="customer_id is required when booking as Administrator."
            )
        # EC-17: Verify customer ID exists
        cust = db.scalar(select(Customer).where(Customer.customer_id == parcel_in.customer_id))
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found."
            )
        target_customer_id = parcel_in.customer_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Delivery agents cannot book parcels."
        )

    # 2. Calculate official delivery charge based on weight tiers
    calculated_charge = calculate_shipping_charge(parcel_in.weight_kg)

    # 3. Generate unique tracking ID
    tracking_id = generate_unique_tracking_id(db)

    # 4. Atomic Multi-Table Insert Transaction
    try:
        # Step A: Parcel record
        new_parcel = Parcel(
            tracking_id=tracking_id,
            customer_id=target_customer_id,
            sender_name=parcel_in.sender_name,
            sender_phone=parcel_in.sender_phone,
            receiver_name=parcel_in.receiver_name,
            receiver_phone=parcel_in.receiver_phone,
            receiver_address=parcel_in.receiver_address,
            source_city=parcel_in.source_city,
            destination_city=parcel_in.destination_city,
            parcel_type=parcel_in.parcel_type.value,
            weight_kg=parcel_in.weight_kg,
            description=parcel_in.description,
            charge=calculated_charge,
            booked_at=datetime.now()
        )
        db.add(new_parcel)
        db.flush()  # Generate new_parcel.parcel_id

        # Step B: Initial parcel status ('Booked')
        initial_status = ParcelStatus(
            parcel_id=new_parcel.parcel_id,
            status="Booked",
            location=f"{parcel_in.source_city} Central Booking Office",
            updated_at=datetime.now()
        )
        db.add(initial_status)

        # Step C: Initial payment record (Support COD, UPI, Card, Net Banking)
        chosen_method = (parcel_in.payment_method or "Cash on Delivery").strip()
        is_paid = (parcel_in.payment_status or "").strip().lower() == "paid"
        initial_payment = Payment(
            parcel_id=new_parcel.parcel_id,
            amount=calculated_charge,
            payment_method=chosen_method,
            payment_status="Paid" if is_paid else "Pending",
            paid_at=datetime.now() if is_paid else None
        )
        db.add(initial_payment)

        db.commit()
        db.refresh(new_parcel)

        # Step D: Log initial milestone to MongoDB (NoSQL Event Store)
        pay_note = f"Payment of Rs. {calculated_charge:.2f} settled via {chosen_method}." if is_paid else f"Payment method: {chosen_method} (Pending COD)."
        log_tracking_event(
            tracking_id=new_parcel.tracking_id,
            status="Booked",
            location=f"{parcel_in.source_city} Central Booking Office",
            updated_by=current_user.email,
            notes=f"Parcel booked and shipment initiated. {pay_note}"
        )

        return build_parcel_response(new_parcel)

    except HTTPException:
        # Re-raise FastAPI HTTP exceptions — do NOT convert them to 500
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to book parcel: {str(e)}"
        )


# -----------------------------------------------------------------------------
# 2. LIST PARCELS (Role-Filtered, Searchable & Paginated)
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[ParcelResponse],
    summary="List parcels (Customers see their own; Admins see all)"
)
def list_parcels(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (e.g. Booked, In Transit)"),
    city: Optional[str] = Query(None, description="Filter by destination city"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists parcels based on caller role:
    - Customer: Only sees parcels they booked.
    - Delivery: Sees assigned deliveries.
    - Admin: Sees all parcels across the system.
    """
    # Fix: use outerjoin so parcels without a status record are still returned
    if current_user.role == "delivery":
        if not current_user.delivery_person:
            return []
        # For delivery role: join both Delivery assignment and ParcelStatus
        query = (
            select(Parcel)
            .join(Delivery, Delivery.parcel_id == Parcel.parcel_id)
            .outerjoin(ParcelStatus, ParcelStatus.parcel_id == Parcel.parcel_id)
            .where(Delivery.delivery_person_id == current_user.delivery_person.delivery_person_id)
        )
    else:
        # For customer and admin: just outerjoin status for filtering
        query = select(Parcel).outerjoin(ParcelStatus, ParcelStatus.parcel_id == Parcel.parcel_id)
        if current_user.role == "customer":
            if not current_user.customer:
                return []
            query = query.where(Parcel.customer_id == current_user.customer.customer_id)
        # admin sees all parcels — no additional where clause needed

    # Optional Filters
    if status_filter:
        query = query.where(ParcelStatus.status.ilike(f"%{status_filter.strip()}%"))

    if city:
        query = query.where(Parcel.destination_city.ilike(f"%{city.strip()}%"))

    query = query.order_by(Parcel.parcel_id.desc()).offset(skip).limit(limit)
    parcels = db.scalars(query).all()

    return [build_parcel_response(p) for p in parcels]


# -----------------------------------------------------------------------------
# 3. GET SINGLE PARCEL DETAILS
# -----------------------------------------------------------------------------
@router.get(
    "/{parcel_id}",
    response_model=ParcelResponse,
    summary="Get parcel details by ID"
)
def get_parcel(
    parcel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves full details for a single parcel:
    - Non-admin customers can only view their own booked parcels.
    - Returns 404 Not Found if parcel does not exist.
    """
    parcel = db.scalar(select(Parcel).where(Parcel.parcel_id == parcel_id))
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found."
        )

    # Permission check for customers
    if current_user.role == "customer":
        if not current_user.customer or parcel.customer_id != current_user.customer.customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You can only view your own parcels."
            )
    elif current_user.role == "delivery":
        ensure_delivery_agent_owns_parcel(parcel_id, current_user, db)

    return build_parcel_response(parcel)


# -----------------------------------------------------------------------------
# 4. UPDATE PARCEL STATUS (Staff / Admin Only)
# -----------------------------------------------------------------------------
@router.put(
    "/{parcel_id}/status",
    response_model=ParcelResponse,
    summary="Update parcel status and current location (Staff/Admin only)"
)
def update_parcel_status_endpoint(
    parcel_id: int,
    status_update: ParcelStatusUpdate,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """
    Updates status and current location of a parcel:
    - Restricted to Admin and Delivery staff.
    - Updates `parcel_status` in MySQL, which automatically FIRES the
      `trg_after_status_update` database trigger and logs into `parcel_status_audit`!
    - When new status is 'Delivered', automatically records `delivery.delivered_at = NOW()`.
    - Logs an append-only timeline event in MongoDB `tracking_history` collection.
    """
    parcel = db.scalar(
        select(Parcel).where(Parcel.parcel_id == parcel_id).with_for_update()
    )
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found."
        )

    ensure_delivery_agent_owns_parcel(parcel_id, current_user, db)

    current_status = parcel.status.status if parcel.status else "Booked"
    target_status = status_update.status.strip()

    # EC-22: Validate that the target status is a recognised milestone
    valid_statuses = {s.value for s in ParcelDeliveryStatus}
    if target_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status value '{target_status}'. Allowed values: {sorted(valid_statuses)}"
        )

    # Completed states cannot be reopened.
    if current_status in ("Delivered", "Returned"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot update status of a delivered parcel."
                if current_status == "Delivered"
                else "Cannot update status of a returned parcel."
            )
        )

    # EC-24: Enforce valid state transition hierarchy
    allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])
    if target_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{current_status}' to '{target_status}'."
        )

    if not parcel.status:
        status_rec = ParcelStatus(
            parcel_id=parcel.parcel_id,
            status=target_status,
            location=status_update.location,
            updated_at=datetime.now()
        )
        db.add(status_rec)
    else:
        parcel.status.status = target_status
        parcel.status.location = status_update.location
        parcel.status.updated_at = datetime.now()

    # If delivered, record delivery timestamp
    if target_status.strip().title() == "Delivered":
        if parcel.delivery and parcel.delivery.delivered_at is None:
            parcel.delivery.delivered_at = datetime.now()

    db.commit()
    db.refresh(parcel)

    # Log milestone event into MongoDB
    log_tracking_event(
        tracking_id=parcel.tracking_id,
        status=target_status,
        location=status_update.location,
        updated_by=current_user.email,
        notes=status_update.notes
    )

    return build_parcel_response(parcel)
