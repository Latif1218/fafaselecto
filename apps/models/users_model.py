from sqlalchemy import Column, String, Boolean, TIMESTAMP, text, DateTime, Integer, Enum
from datetime import datetime
from sqlalchemy.orm import relationship
from ..database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum as PyEnum



class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"
    TUTOR = "tutor"


class UserPlan(str, PyEnum):
    ESSENTIAL = "essential"
    STARTER = "starter"
    PREMIUM = "premium"
    ULTIMATE = "ultimate"



class UserStatus(str, PyEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"



class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    plan = Column(Enum(UserPlan), default=UserPlan.ESSENTIAL, nullable=False)
    sector = Column(String(100), nullable=True)
    short_description = Column(String(500), nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    cv_count = Column(Integer, default=0)
    last_activity = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_otp = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    


    cvs = relationship("CV", back_populates="user", cascade="all, delete")
    cv_forms = relationship("CVForm", back_populates="user", cascade="all, delete")
    cover_letters = relationship("CoverLetter", back_populates="user", cascade="all, delete")
    reset_code = relationship("PasswordResetCode", back_populates="user")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    ultimate_requests = relationship(
        "UltimateRequest",
        foreign_keys="[UltimateRequest.user_id]",
        back_populates="user",
        cascade="all, delete-orphan"  
    )
    assigned_reviews = relationship(
        "UltimateRequest",
        foreign_keys="[UltimateRequest.assigned_tutor_id]",
        back_populates="tutor",
        cascade="all, delete-orphan" 
    )