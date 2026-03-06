from sqlalchemy import Column, String, Enum, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base
from enum import Enum as PyEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid



class PlanType(str, PyEnum):
    ESSENTIAL = "essential"
    STARTER = "starter"
    PREMIUM = "premium"
    ULTIMATE = "ultimate"


class SubscriptionStatus(str, PyEnum):
    INACTIVE = "inactive"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    stripe_subscription_id = Column(String, nullable=True, index=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    plan_type = Column(Enum(PlanType), nullable=False, default=PlanType.ESSENTIAL)
    price_id = Column(String, nullable=True)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.INACTIVE)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")