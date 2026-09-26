"""
backend/models/delivery_person.py
=============================================================================
SQLAlchemy ORM Model: `delivery_person` table
=============================================================================
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class DeliveryPerson(Base):
    __tablename__ = "delivery_person"

    delivery_person_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)
    vehicle_number = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # 1-to-1 Relationship back to User
    user = relationship("User", back_populates="delivery_person")

    # 1-to-Many Relationship with Deliveries handled by this agent
    deliveries = relationship("Delivery", back_populates="delivery_person")

    def __repr__(self):
        return f"<DeliveryPerson(id={self.delivery_person_id}, name='{self.full_name}', active={self.is_active})>"
