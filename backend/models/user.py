"""
backend/models/user.py
=============================================================================
SQLAlchemy ORM Model: `user` table
=============================================================================
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SQLEnum("customer", "admin", "delivery", name="user_role_enum"),
        nullable=False,
        default="customer"
    )
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 1-to-1 Relationship with Customer
    customer = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # 1-to-1 Relationship with DeliveryPerson
    delivery_person = relationship("DeliveryPerson", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email='{self.email}', role='{self.role}')>"
