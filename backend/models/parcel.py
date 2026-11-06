"""
backend/models/parcel.py
=============================================================================
SQLAlchemy ORM Model: `parcel` table
=============================================================================
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Parcel(Base):
    __tablename__ = "parcel"

    parcel_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    tracking_id = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customer.customer_id", ondelete="RESTRICT"), nullable=False, index=True)
    sender_name = Column(String(100), nullable=False)
    sender_phone = Column(String(15), nullable=False)
    receiver_name = Column(String(100), nullable=False)
    receiver_phone = Column(String(15), nullable=False)
    receiver_address = Column(String(255), nullable=True)
    source_city = Column(String(50), nullable=False)
    destination_city = Column(String(50), nullable=False)
    parcel_type = Column(String(50), nullable=False)
    weight_kg = Column(Numeric(6, 2), nullable=False)
    description = Column(Text, nullable=True)
    charge = Column(Numeric(10, 2), nullable=False)
    booked_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="parcels")
    status = relationship("ParcelStatus", back_populates="parcel", uselist=False, cascade="all, delete-orphan")
    delivery = relationship("Delivery", back_populates="parcel", uselist=False, cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="parcel", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Parcel(id={self.parcel_id}, tracking='{self.tracking_id}', "
            f"from='{self.source_city}', to='{self.destination_city}', weight={self.weight_kg})>"
        )
