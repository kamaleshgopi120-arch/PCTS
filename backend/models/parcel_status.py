"""
backend/models/parcel_status.py
=============================================================================
SQLAlchemy ORM Model: `parcel_status` table
=============================================================================
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class ParcelStatus(Base):
    __tablename__ = "parcel_status"

    status_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    parcel_id = Column(Integer, ForeignKey("parcel.parcel_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    status = Column(String(30), nullable=False)
    location = Column(String(100), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 1-to-1 Relationship back to Parcel
    parcel = relationship("Parcel", back_populates="status")

    def __repr__(self):
        return f"<ParcelStatus(parcel_id={self.parcel_id}, status='{self.status}', location='{self.location}')>"
