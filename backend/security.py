"""
backend/security.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 10
Security, Cryptographic Password Hashing (bcrypt), and JWT Authentication
=============================================================================

What you learn in this file:
1. Why passwords must NEVER be stored as plain text (we use bcrypt cryptographic salted hashing).
2. What a JWT (JSON Web Token) is:
   - A digitally signed token consisting of: Header.Payload.Signature
   - The server verifies the signature using a secret key (HS256) without needing a server-side session store.
3. How OAuth2 Bearer token authentication works with FastAPI.
4. Role-Based Access Control (RBAC): Restricting administrative endpoints to users with role='admin'.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from dotenv import load_dotenv

from backend.database import get_db
from backend.models.user import User

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pcts_super_secure_jwt_secret_key_32_bytes_long_college_project")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# FastAPI OAuth2 scheme: Tells Swagger UI where clients obtain bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# -----------------------------------------------------------------------------
# 1. PASSWORD HASHING AND VERIFICATION (bcrypt)
# -----------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    """
    Hashes a plain text password using bcrypt with a randomized salt.
    Each call generates a different hash even for the same password!
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies that a plain text password matches the stored bcrypt hash.
    Constant-time comparison prevents timing attacks.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


# -----------------------------------------------------------------------------
# 2. JWT TOKEN GENERATION AND DECODING
# -----------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a cryptographically signed JWT token with an expiration timestamp.
    """
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now_utc
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodes and validates a JWT token signature and expiration.
    Raises HTTPException 401 if invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise credentials_exception


# -----------------------------------------------------------------------------
# 3. CURRENT USER DEPENDENCY
# -----------------------------------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts the Bearer token from the HTTP Authorization header,
    validates it, and fetches the authenticated User object from the MySQL database.
    """
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    email = payload.get("sub")

    if user_id is None or email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(select(User).where(User.user_id == user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# -----------------------------------------------------------------------------
# 4. ROLE-BASED ACCESS CONTROL (RBAC) DEPENDENCY FACTORY
# -----------------------------------------------------------------------------
class RoleChecker:
    """
    Dependency callable that verifies whether the authenticated user has one of
    the allowed roles. Enforces EC-04 from edge_case.md.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: You do not have permission to access this resource. (Requires role in: {self.allowed_roles})"
            )
        return current_user


# Convenience shortcuts for endpoint protection
require_admin = RoleChecker(["admin"])
require_customer = RoleChecker(["customer"])
require_delivery = RoleChecker(["delivery"])
require_staff = RoleChecker(["admin", "delivery"])
