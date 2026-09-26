"""
backend/models/payment.py
=============================================================================
SQLAlchemy ORM Model: `payment` table
=============================================================================
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Enum as SQLEnum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Payment(Base):
    __tablename__ = "payment"

    payment_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    parcel_id = Column(Integer, ForeignKey("parcel.parcel_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(30), nullable=True)
    payment_status = Column(
        SQLEnum("Pending", "Paid", "Failed", name="payment_status_enum"),
        nullable=False,
        default="Pending"
    )
    paid_at = Column(DateTime, nullable=True)

    # 1-to-1 Relationship back to Parcel
    parcel = relationship("Parcel", back_populates="payment")

    def __repr__(self):
        return f"<Payment(id={self.payment_id}, parcel_id={self.parcel_id}, amount={self.amount}, status='{self.payment_status}')>"
