from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from ..database import Base
import uuid




class CV(Base):
    __tablename__ = "cv"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(150), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), default="pdf")
    score = Column(Integer, nullable=True)
    tips = Column(JSON, nullable=True)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    user = relationship("User", back_populates="cvs")
    ultimate_requests = relationship(
        "UltimateRequest",
        back_populates="cv",
        cascade="all, delete-orphan"
    )


class CVForm(Base):   
    __tablename__ = "cv_forms"   
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    personal_details = Column(JSON)
    education = Column(JSON)
    employment = Column(JSON)
    languages = Column(JSON)
    skills = Column(JSON)
    activities = Column(JSON)
    last_updated_step = Column(String(50), nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    user = relationship("User", back_populates="cv_forms")




class CoverLetter(Base):
    __tablename__ = "cover_letter"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cv.id"), nullable=True)
    title = Column(String(150), nullable=True)
    content = Column(String, nullable=False)
    file_path = Column(String(500), nullable=True)
    language = Column(String(20), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="cover_letters")
    cv = relationship("CV")