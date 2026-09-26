"""
backend/models/customer.py
=============================================================================
SQLAlchemy ORM Model: `customer` table
=============================================================================
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Customer(Base):
    __tablename__ = "customer"

    customer_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(50), nullable=True)

    # 1-to-1 Relationship back to User
    user = relationship("User", back_populates="customer")

    # 1-to-Many Relationship with Parcels booked by this customer
    parcels = relationship("Parcel", back_populates="customer")

    def __repr__(self):
        return f"<Customer(customer_id={self.customer_id}, name='{self.full_name}', city='{self.city}')>"
