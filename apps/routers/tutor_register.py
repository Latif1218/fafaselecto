from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import re

from ..database import get_db
from ..models import users_model
from ..schemas import users_schema
from ..utils import hashing, otp_and_mail
from ..config import EMAIL_REGEX


router = APIRouter(
    prefix="/tutor",
    tags=["Tutor"]
)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_tutor(
    tutor: users_schema.TutorCreate,
    db: Session = Depends(get_db)
):

    if not re.match(EMAIL_REGEX, tutor.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid email format"
        )

    existing_user = db.query(users_model.User).filter(
        users_model.User.email == tutor.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )

    hashed_password = hashing.hash_password(tutor.password)

    otp = otp_and_mail.generate_otp()
    otp_expire = datetime.utcnow() + timedelta(minutes=10)

    new_tutor = users_model.User(
        email=tutor.email,
        full_name=tutor.full_name,
        password=hashed_password,
        role=users_model.UserRole.TUTOR,
        sector=tutor.sector,
        short_description=tutor.short_description,
        email_otp=otp,
        otp_expires_at=otp_expire,
        is_verified=False
    )

    db.add(new_tutor)
    db.commit()
    db.refresh(new_tutor)

    otp_and_mail.send_otp_email(new_tutor.email, otp)

    return {
        "message": "Tutor registered successfully"
    }


@router.post("/verify_tutor_otp")
def verify_otp(data: users_schema.VerifyOTP, db: Session = Depends(get_db)):

    user = db.query(users_model.User).filter(
        users_model.User.email == data.email
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    if user.email_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    user.is_verified = True
    user.email_otp = None
    user.otp_expires_at = None

    db.commit()

    return {"message": "Email verified successfully"}