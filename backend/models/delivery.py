"""
backend/models/delivery.py
=============================================================================
SQLAlchemy ORM Model: `delivery` table
=============================================================================
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Delivery(Base):
    __tablename__ = "delivery"

    delivery_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    parcel_id = Column(Integer, ForeignKey("parcel.parcel_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    delivery_person_id = Column(Integer, ForeignKey("delivery_person.delivery_person_id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=datetime.now, nullable=False)
    delivered_at = Column(DateTime, nullable=True)

    # Relationships
    parcel = relationship("Parcel", back_populates="delivery")
    delivery_person = relationship("DeliveryPerson", back_populates="deliveries")

    def __repr__(self):
        return f"<Delivery(delivery_id={self.delivery_id}, parcel_id={self.parcel_id}, agent_id={self.delivery_person_id})>"
