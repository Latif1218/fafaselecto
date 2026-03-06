from fastapi import APIRouter, Depends, status, HTTPException
from ..authentication import users_oauth
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Annotated
from ..database import get_db, get_redis
from ..schemas import forgot_password_schema
from ..models.users_model import User
from ..models.forgot_password_model import PasswordResetCode
from ..utils import otp_and_mail, hashing
from ..authentication.users_oauth import get_current_user


router = APIRouter(
    prefix="/forgot",
    tags=["Forgot - Password"]
)


@router.post("forgot_pass", status_code=status.HTTP_200_OK)
def forget_password(
    payload: forgot_password_schema.ForgotPasswoedRequest,
    db: Annotated[Session, Depends(get_db)]
):
    user = (
        db.query(User).filter_by(email=payload.email).first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
    
    otp_code = otp_and_mail.generate_otp()

    db.execute(
        delete(PasswordResetCode).where(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.used.is_(False)
        )
    )

    otp_record = PasswordResetCode(
        user_id = user.id,
        otp = otp_code,
        used = False,
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    sent = otp_and_mail.send_otp_email(to_email=user.email, otp=otp_code)

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        )
    
    return {
        "status" : "success",
        "message" : f"Password reset OTP sent to {user.email}"
    }




@router.post("/verify_otp", status_code=status.HTTP_200_OK)
def verify_otp(
    payload: forgot_password_schema.OTPVerify,
    db: Annotated[Session, Depends(get_db)]
):
    user = db.query(User).filter(
        User.email == payload.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email dose not exist"
        )
    
    otp_record = db.scalars(
        select(PasswordResetCode).where(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.otp == payload.otp,
            PasswordResetCode.used.is_(False),
            PasswordResetCode.expires_at > datetime.now(timezone.utc)
        ).limit(1)
    ).first()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OD expired OTP"
        )
    
    otp_record.used = True
    db.commit()

    redis_session = get_redis()
    reset_key = redis_session.get_key("password_reset: {}:{}", payload.email, payload.otp)
    redis_session.set_with_expiry(reset_key, "verified", 600)
    
    return {
        "status" : "success",
        "message": "OTP verified successfully. you can now reset your password."
    }




@router.put("update_password_without_token", status_code=status.HTTP_200_OK)
def update_password_without_token(
    payload: forgot_password_schema.PasswordUpdateWithoutToken,
    db: Annotated[Session, Depends(get_db)]
):
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    user = db.query(User).filter(User.email == payload.email).first()
    if not user: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not exist"
        )
    
    redis_session = get_redis()
    reset_key = redis_session.get(f"password_reset: {payload.email}:{payload.otp}")

    reset_verified = redis_session.get_key(reset_key)
    if not reset_verified:
        otp_record = db.query(PasswordResetCode).filter(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.otp == payload.otp,
            PasswordResetCode.expires_at > datetime.now(timezone.utc)
        ).first()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP not verified or expired"
            )
        
    else:
        redis_session.delete(reset_key)

    hashed_password = hashing.hash_password(payload.new_password)
    user.password = hashed_password

    db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user.id,
        PasswordResetCode.used == False
    ).delete()

    try: 
        db.commit()

        user_session_key = redis_session.get_key("user_session: {}", user.id)
        redis_session.delete(user_session_key)

        return {
            "status": "success",
            "message": "Password update successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )





@router.put("update_password", status_code=status.HTTP_200_OK)
def update_password(
    payload: forgot_password_schema.PasswordUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    user = db.query(User).filter(
        User.id == user.id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user does not exist"
        )
    db.commit()

    return {
        "status" : "Success",
        "message" : "Password update successfully."
    }