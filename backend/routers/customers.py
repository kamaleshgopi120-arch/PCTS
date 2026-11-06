"""
backend/routers/customers.py
=============================================================================
Customer Management CRUD API Endpoints
=============================================================================
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from backend.database import get_db
from backend.models.user import User
from backend.models.customer import Customer
from backend.models.parcel import Parcel
from backend.schemas.customer import CustomerUpdate, CustomerResponse
from backend.security import get_current_user, require_admin

router = APIRouter(prefix="/api/customers", tags=["Customer Management"])


# -----------------------------------------------------------------------------
# 1. LIST ALL CUSTOMERS (Admin Only, Paginated & Searchable)
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[CustomerResponse],
    summary="List all registered customers (Admin only)",
    dependencies=[Depends(require_admin)]
)
def list_customers(
    skip: int = Query(0, ge=0, description="Records to skip (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    city: Optional[str] = Query(None, description="Filter by city"),
    search: Optional[str] = Query(None, description="Search by name or phone"),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of customers.
    Restricted to system administrators.
    """
    query = select(Customer)

    if city:
        query = query.where(Customer.city.ilike(f"%{city.strip()}%"))

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Customer.full_name.ilike(search_pattern),
                Customer.phone.ilike(search_pattern)
            )
        )

    query = query.order_by(Customer.customer_id.asc()).offset(skip).limit(limit)
    customers = db.scalars(query).all()

    # Populate email from linked User object
    result = []
    for c in customers:
        resp = CustomerResponse.model_validate(c)
        if c.user:
            resp.email = c.user.email
        result.append(resp)

    return result


# -----------------------------------------------------------------------------
# 2. GET SINGLE CUSTOMER DETAILS
# -----------------------------------------------------------------------------
@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Get customer details by Customer ID"
)
def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves details for a specific customer.
    - Non-admin users can only view their own profile.
    - Enforces EC-08: If the customer does not exist, returns 404 Not Found.
    """
    # EC-08: Check if customer exists FIRST (404 before 403 — do not leak existence)
    customer = db.scalar(select(Customer).where(Customer.customer_id == customer_id))
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found."
        )

    # Permission check: If customer role, must own this profile
    if current_user.role != "admin":
        if not current_user.customer or current_user.customer.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You can only view your own customer profile."
            )

    resp = CustomerResponse.model_validate(customer)
    if customer.user:
        resp.email = customer.user.email
    return resp


# -----------------------------------------------------------------------------
# 3. UPDATE CUSTOMER PROFILE
# -----------------------------------------------------------------------------
@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update customer profile details"
)
def update_customer(
    customer_id: int,
    update_data: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates full_name, phone, address, or city for an existing customer.
    - Customers can update their own details. Admins can update any customer.
    - Enforces EC-08: 404 Not Found if customer does not exist.
    - Enforces EC-10: Phone number validated by Pydantic schema.
    """
    if current_user.role != "admin":
        if not current_user.customer or current_user.customer.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You can only update your own customer profile."
            )

    customer = db.scalar(select(Customer).where(Customer.customer_id == customer_id))
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found."
        )

    # Apply updates for fields provided by client
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        if val is not None:
            setattr(customer, field, val)

    db.commit()
    db.refresh(customer)

    resp = CustomerResponse.model_validate(customer)
    if customer.user:
        resp.email = customer.user.email
    return resp


# -----------------------------------------------------------------------------
# 4. DELETE CUSTOMER PROFILE
# -----------------------------------------------------------------------------
@router.delete(
    "/{customer_id}",
    summary="Delete a customer profile (Admin only)",
    dependencies=[Depends(require_admin)]
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """
    Deletes a customer from the database.
    - Restricted to Admins.
    - Enforces EC-08: 404 Not Found if customer does not exist.
    - Enforces EC-11: Cannot delete a customer who has existing parcel records.
    """
    customer = db.scalar(select(Customer).where(Customer.customer_id == customer_id))
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found."
        )

    # EC-11: Check if customer has any booked parcels
    parcel_count = db.scalar(
        select(func.count(Parcel.parcel_id)).where(Parcel.customer_id == customer_id)
    )
    if parcel_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete customer with existing parcels."
        )

    # Delete customer and linked user account
    user_to_delete = customer.user
    db.delete(customer)
    if user_to_delete:
        db.delete(user_to_delete)

    db.commit()

    return {
        "message": "Customer deleted successfully.",
        "customer_id": customer_id
    }
