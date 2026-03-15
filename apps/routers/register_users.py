# routers/register_user.py
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..models import users_model
from ..schemas import users_schema
from ..database import get_db
from ..utils import hashing, otp_and_mail
from ..config import DOMAIN, EMAIL_REGEX
import re


router = APIRouter(prefix="/register_user", tags=["Registration"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(user: users_schema.UserCreate, db: Session = Depends(get_db)):

    if not re.match(EMAIL_REGEX, user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    existing_user = db.query(users_model.User).filter(
        users_model.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hashing.hash_password(user.password)

    otp = otp_and_mail.generate_otp()

    otp_expires = datetime.utcnow() + timedelta(minutes=10)

    new_user = users_model.User(
        email=user.email,
        full_name=user.full_name,
        password=hashed_password,
        email_otp=otp,
        otp_expires_at=otp_expires,
        is_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    otp_and_mail.send_otp_email(new_user.email, otp)

    return {
        "message": "User created. OTP sent to email."
    }






@router.post("/verify_otp")
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