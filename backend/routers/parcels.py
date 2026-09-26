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
from backend.models.payment import Payment
from backend.schemas.parcel import (
    ParcelCreate,
    ParcelResponse,
    calculate_shipping_charge
)
from backend.security import get_current_user

router = APIRouter(prefix="/api/parcels", tags=["Parcel Booking & Management"])


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

    # Fallback to high-precision timestamp if random retries collide
    micro = datetime.now().strftime("%f")[:4]
    return f"PCTS-{date_str}-{micro}"


# -----------------------------------------------------------------------------
# HELPER: Build ParcelResponse with Status and Payment Details
# -----------------------------------------------------------------------------
def build_parcel_response(parcel: Parcel) -> ParcelResponse:
    return ParcelResponse(
        parcel_id=parcel.parcel_id,
        tracking_id=parcel.tracking_id,
        customer_id=parcel.customer_id,
        sender_name=parcel.sender_name,
        sender_phone=parcel.sender_phone,
        receiver_name=parcel.receiver_name,
        receiver_phone=parcel.receiver_phone,
        source_city=parcel.source_city,
        destination_city=parcel.destination_city,
        parcel_type=parcel.parcel_type,
        weight_kg=float(parcel.weight_kg),
        description=parcel.description,
        charge=float(parcel.charge),
        booked_at=parcel.booked_at,
        status=parcel.status.status if parcel.status else "Booked",
        location=parcel.status.location if parcel.status else None,
        payment_status=parcel.payment.payment_status if parcel.payment else "Pending",
        payment_amount=float(parcel.payment.amount) if parcel.payment else float(parcel.charge)
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

        # Step C: Initial payment record ('Pending')
        initial_payment = Payment(
            parcel_id=new_parcel.parcel_id,
            amount=calculated_charge,
            payment_method="Cash on Delivery",
            payment_status="Pending"
        )
        db.add(initial_payment)

        db.commit()
        db.refresh(new_parcel)

        return build_parcel_response(new_parcel)

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
    query = select(Parcel).join(Parcel.status)

    if current_user.role == "customer":
        if not current_user.customer:
            return []
        query = query.where(Parcel.customer_id == current_user.customer.customer_id)

    elif current_user.role == "delivery":
        if current_user.delivery_person:
            # Join with delivery assignment
            query = query.join(Parcel.delivery).where(
                Parcel.delivery.has(delivery_person_id=current_user.delivery_person.delivery_person_id)
            )

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

    return build_parcel_response(parcel)
