"""
backend/routers/payments.py — Payment Management API Endpoints
=============================================================================
This router handles payment viewing, status updates, and settlement records.

Enforces Edge Cases from edge_case.md:
- EC-30: Cannot record/update payment for a parcel that already has a 'Paid' status (400 Bad Request).
- EC-31: Payment amount must be strictly greater than 0 (422 Unprocessable Entity / 400 Bad Request).
- EC-32: Payment query for a parcel ID that does not exist (404 Not Found).
- EC-33: Payment record does not exist (404 Not Found).
=============================================================================
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models.user import User
from backend.models.parcel import Parcel
from backend.models.payment import Payment
from backend.mongo import log_tracking_event
from backend.security import (
    get_current_user,
    require_admin,
)
from backend.schemas.payment import (
    PaymentStatus,
    PaymentUpdate,
    PaymentResponse
)

router = APIRouter(prefix="/api/payments", tags=["Payment Management"])


def ensure_payment_access(payment: Payment, current_user: User) -> None:
    if current_user.role == "admin":
        return

    parcel = payment.parcel
    if (
        current_user.role != "customer"
        or not current_user.customer
        or not parcel
        or parcel.customer_id != current_user.customer.customer_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view payments for your own parcels."
        )


def build_payment_response(p: Payment) -> PaymentResponse:
    """Helper to convert Payment ORM model to PaymentResponse schema."""
    parcel = p.parcel
    customer_name = parcel.customer.full_name if (parcel and parcel.customer) else None
    receiver_name = parcel.receiver_name if parcel else None
    tracking_id = parcel.tracking_id if parcel else ""

    return PaymentResponse(
        payment_id=p.payment_id,
        parcel_id=p.parcel_id,
        tracking_id=tracking_id,
        amount=float(p.amount),
        payment_method=p.payment_method,
        payment_status=p.payment_status,
        paid_at=p.paid_at,
        customer_name=customer_name,
        receiver_name=receiver_name
    )


# -----------------------------------------------------------------------------
# 1. LIST ALL PAYMENTS (Admin Only)
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[PaymentResponse],
    summary="List all payments (Admin only)",
    dependencies=[Depends(require_admin)]
)
def list_payments(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Pending, Paid, Failed)"),
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(20, ge=1, le=100, description="Limit"),
    db: Session = Depends(get_db)
):
    """Admin endpoint to view and filter payments across all parcels."""
    query = select(Payment).order_by(Payment.payment_id.desc())

    if status_filter:
        query = query.where(Payment.payment_status.ilike(status_filter.strip()))

    payments = db.scalars(query.offset(skip).limit(limit)).all()
    return [build_payment_response(p) for p in payments]


# -----------------------------------------------------------------------------
# 2. CREATE NEW PAYMENT RECORD (POST /api/payments)
# -----------------------------------------------------------------------------
@router.post(
    "",
    response_model=PaymentResponse,
    summary="Create a new payment record (Admin only)",
    status_code=status.HTTP_201_CREATED
)
def create_payment(
    payload: PaymentUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new payment record for a parcel:
    - EC-32: Validates parcel exists (404 Not Found).
    - EC-30: Rejects if payment already exists for this parcel.
    - EC-31: Validates amount > 0 (400 Bad Request).
    """
    # Validate payload has required fields
    if not payload.parcel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="parcel_id is required."
        )
    
    if not payload.amount or payload.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than 0."
        )

    # EC-32: Verify parcel exists
    parcel = db.scalar(select(Parcel).where(Parcel.parcel_id == payload.parcel_id))
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found."
        )

    # EC-30: Check if payment already exists
    existing = db.scalar(select(Payment).where(Payment.parcel_id == payload.parcel_id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment record already exists for this parcel."
        )

    # Validate amount matches parcel charge
    expected_amount = Decimal(parcel.charge).quantize(Decimal("0.01"))
    if payload.amount != expected_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount must match the parcel charge of Rs. {expected_amount:.2f}."
        )

    # Create payment record
    new_payment = Payment(
        parcel_id=payload.parcel_id,
        amount=payload.amount,
        payment_method=payload.payment_method or "Cash",
        payment_status=payload.payment_status.value if payload.payment_status else "Pending",
        paid_at=datetime.now() if (payload.payment_status and payload.payment_status.value == "Paid") else None
    )

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return build_payment_response(new_payment)


# -----------------------------------------------------------------------------
# 3. GET PAYMENT BY PAYMENT ID (GET /api/payments/id/{payment_id})
# NOTE: This route MUST come before /{parcel_id} — FastAPI matches routes in
#       declaration order. If /{parcel_id} is first, "id" gets parsed as an
#       integer parcel_id and this route is never reached.
# -----------------------------------------------------------------------------
@router.get(
    "/id/{payment_id}",
    response_model=PaymentResponse,
    summary="View payment details by Payment ID"
)
def get_payment_by_id(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve payment directly by payment_id:
    - EC-33: Returns 404 if record does not exist.
    - Customers can only view their own payment.
    """
    payment = db.scalar(select(Payment).where(Payment.payment_id == payment_id))
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found."
        )

    ensure_payment_access(payment, current_user)

    return build_payment_response(payment)


# -----------------------------------------------------------------------------
# 4. VIEW PAYMENT FOR A PARCEL (GET /api/payments/{parcel_id})
# NOTE: This route comes AFTER /id/{payment_id} to avoid shadowing it.
# -----------------------------------------------------------------------------
@router.get(
    "/{parcel_id}",
    response_model=PaymentResponse,
    summary="View payment details for a specific parcel"
)
def get_payment_by_parcel(
    parcel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    View payment details for a given parcel:
    - EC-32: Verifies parcel exists (404 Not Found).
    - EC-33: Verifies payment record exists (404 Not Found).
    - Access control: Customers can only view payments for their own parcels.
    """
    # EC-32: Verify parcel exists
    parcel = db.scalar(select(Parcel).where(Parcel.parcel_id == parcel_id))
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found."
        )

    # Permission check for customers
    # EC-33: Verify payment record exists
    payment = parcel.payment
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found."
        )

    ensure_payment_access(payment, current_user)

    return build_payment_response(payment)


# -----------------------------------------------------------------------------
# 5. UPDATE PAYMENT STATUS / SETTLE PAYMENT (PUT /api/payments/id/{payment_id})
# -----------------------------------------------------------------------------
@router.put(
    "/id/{payment_id}",
    response_model=PaymentResponse,
    summary="Update payment status or record settlement (Admin only)"
)
def update_payment(
    payment_id: int,
    payload: PaymentUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Updates or settles a payment record:
    - EC-33: Returns 404 if payment does not exist.
    - EC-30: Rejects update if payment is already 'Paid' (400 Bad Request).
    - EC-31: Validates amount > 0 if amount is provided (422 / 400).
    - When marked 'Paid', sets paid_at timestamp.
    - Keeps payment settlement details out of the public parcel tracking timeline.
    """
    payment = db.scalar(
        select(Payment).where(Payment.payment_id == payment_id).with_for_update()
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found."
        )

    # EC-30: Cannot record or update payment for an already paid parcel
    if payment.payment_status == "Paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already completed for this parcel."
        )

    # A recorded settlement must match the charge calculated at booking.
    if payload.amount is not None:
        if payload.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than 0."
            )
        expected_amount = Decimal(payment.parcel.charge).quantize(Decimal("0.01"))
        if payload.amount != expected_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount must match the parcel charge of Rs. {expected_amount:.2f}."
            )
        payment.amount = payload.amount

    # Update payment method if provided
    if payload.payment_method:
        payment.payment_method = payload.payment_method

    # Update status if provided
    if payload.payment_status:
        target_status = payload.payment_status.value
        payment.payment_status = target_status

        if target_status == "Paid":
            payment.paid_at = datetime.now()

    db.commit()
    db.refresh(payment)

    return build_payment_response(payment)


# -----------------------------------------------------------------------------
# 6. INSTANT ONLINE SETTLEMENT BY TRACKING ID (POST /api/payments/pay-online/{tracking_id})
# -----------------------------------------------------------------------------
@router.post(
    "/pay-online/{tracking_id}",
    response_model=PaymentResponse,
    summary="Settle pending payment online via UPI or Card"
)
def settle_payment_online(
    tracking_id: str,
    payload: PaymentUpdate,
    db: Session = Depends(get_db)
):
    """
    Allows a customer or sender to settle an outstanding delivery charge online
    using simulated UPI, Credit/Debit Card, or Net Banking.
    - Settle payment to 'Paid'
    - Updates paid_at timestamp
    - Emits milestone to MongoDB tracking audit
    """
    cleaned_id = tracking_id.strip().upper()
    parcel = db.scalar(select(Parcel).where(Parcel.tracking_id == cleaned_id).with_for_update())
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel with tracking ID {cleaned_id} not found."
        )

    payment = parcel.payment
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found for this parcel."
        )

    if payment.payment_status == "Paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is already completed for this parcel."
        )

    method = payload.payment_method or "UPI"
    payment.payment_method = method
    payment.payment_status = "Paid"
    payment.paid_at = datetime.now()

    db.commit()
    db.refresh(payment)

    # Log payment settlement to MongoDB tracking history
    log_tracking_event(
        tracking_id=parcel.tracking_id,
        status=parcel.status.status if parcel.status else "In Transit",
        location=parcel.status.location if parcel.status else parcel.source_city,
        updated_by="Payment Gateway (Instant Online)",
        notes=f"Delivery charge of Rs. {float(payment.amount):.2f} successfully settled via {method}."
    )

    return build_payment_response(payment)

