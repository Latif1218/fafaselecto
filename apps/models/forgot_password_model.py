from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from ..database import Base
from sqlalchemy.orm import relationship
from cuid2 import Cuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

cuid = Cuid()


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    otp = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="reset_code")