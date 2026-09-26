"""
backend/routers/auth.py
=============================================================================
User Authentication and Authorization API Endpoints
=============================================================================
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from backend.database import get_db
from backend.models.user import User
from backend.models.customer import Customer
from backend.models.delivery_person import DeliveryPerson
from backend.schemas.user import (
    UserRegisterRequest,
    UserLogin,
    Token,
    UserResponse,
    UserDetailResponse,
    UserRole
)
from backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_admin
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# -----------------------------------------------------------------------------
# 1. USER REGISTRATION
# -----------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and create their profile"
)
def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registers a new user in the MySQL database:
    - Enforces EC-05: Rejects duplicate emails with 400 Bad Request.
    - Hashes the password with bcrypt (never stores plain text).
    - Atomically creates the User and associated Customer or DeliveryPerson profile.
    """
    # EC-05: Check if email already exists
    existing_user = db.scalar(select(User).where(User.email == user_data.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered."
        )

    # Hash the password using bcrypt
    hashed_pw = hash_password(user_data.password)

    # Create the User record
    new_user = User(
        email=user_data.email,
        password_hash=hashed_pw,
        role=user_data.role.value
    )
    db.add(new_user)
    db.flush()  # Flushes to MySQL to generate new_user.user_id

    # Create profile based on selected role
    if user_data.role == UserRole.CUSTOMER:
        new_customer = Customer(
            user_id=new_user.user_id,
            full_name=user_data.full_name,
            phone=user_data.phone,
            address=user_data.address,
            city=user_data.city or "Chennai"
        )
        db.add(new_customer)

    elif user_data.role == UserRole.DELIVERY:
        new_delivery_person = DeliveryPerson(
            user_id=new_user.user_id,
            full_name=user_data.full_name,
            phone=user_data.phone,
            vehicle_number=user_data.vehicle_number or "TN-01-XX-0000",
            is_active=True
        )
        db.add(new_delivery_person)

    db.commit()
    db.refresh(new_user)

    return new_user


# -----------------------------------------------------------------------------
# 2. USER LOGIN
# -----------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user and return JWT Bearer token"
)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticates a user:
    - Enforces EC-01 & EC-02: Returns generic "Invalid email or password" error.
    - Generates a signed JWT access token containing user_id, email, and role.
    """
    # Look up user by email
    user = db.scalar(select(User).where(User.email == login_data.email))

    # Verify user exists and password matches
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT Token
    token_payload = {
        "sub": user.email,
        "user_id": user.user_id,
        "role": user.role
    }
    access_token = create_access_token(data=token_payload)

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.user_id,
        email=user.email
    )


# -----------------------------------------------------------------------------
# 3. GET CURRENT LOGGED-IN USER PROFILE
# -----------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserDetailResponse,
    summary="Get profile details of currently authenticated user"
)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Protected route: Returns the profile of the user identified by the Bearer token.
    Enforces EC-07: Requests without a valid token are rejected with 401 Unauthorized.
    """
    detail = UserDetailResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at
    )

    if current_user.role == "customer" and current_user.customer:
        detail.full_name = current_user.customer.full_name
        detail.phone = current_user.customer.phone
        detail.address = current_user.customer.address
        detail.city = current_user.customer.city

    elif current_user.role == "delivery" and current_user.delivery_person:
        detail.full_name = current_user.delivery_person.full_name
        detail.phone = current_user.delivery_person.phone
        detail.vehicle_number = current_user.delivery_person.vehicle_number

    return detail


# -----------------------------------------------------------------------------
# 4. ADMIN-ONLY DEMONSTRATION ENDPOINT
# -----------------------------------------------------------------------------
@router.get(
    "/admin-only",
    summary="Admin-only endpoint demonstrating Role-Based Access Control",
    dependencies=[Depends(require_admin)]
)
def admin_only_dashboard(
    admin_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enforces EC-04: Non-admin users attempting to access this route receive
    HTTP 403 Forbidden.
    """
    total_users = db.scalar(select(func.count(User.user_id)))
    return {
        "message": f"Welcome Administrator ({admin_user.email})!",
        "access": "Granted (admin role verified)",
        "total_registered_users": total_users
    }
