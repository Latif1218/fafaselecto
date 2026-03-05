from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
from datetime import datetime
from enum import Enum as PyEnum


class ReviewStatus(str, PyEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class UltimateRequest(Base):
    __tablename__ = "ultimate_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cv.id"), nullable=False, index=True)
    job_description = Column(String(2000), nullable=True)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    assigned_tutor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    deadline = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="ultimate_requests"
    )
    tutor = relationship(
        "User",
        foreign_keys=[assigned_tutor_id],
        back_populates="assigned_reviews"  
    )

    cv = relationship("CV", back_populates="ultimate_requests")