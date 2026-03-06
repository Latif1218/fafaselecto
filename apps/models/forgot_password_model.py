from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from ..database import Base
from sqlalchemy.orm import relationship
from cuid2 import Cuid
from datetime import datetime

cuid = Cuid()


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="reset_code")