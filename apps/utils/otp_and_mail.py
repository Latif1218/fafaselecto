import smtplib
import secrets
from fastapi import HTTPException, status
from email.message import EmailMessage
from ..config import EMAIL_FROM, EMAIL_HOST, EMAIL_PASSWORD, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_USER
from smtplib import SMTPException, SMTPAuthenticationError


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def send_otp_email(to_email: str, otp: str) -> bool:

    subject = "Your IRON READY OTP Code"
    body = f"""
    Hi,

    Your OTP code is: {otp}

    If you did not fequest this code, pleace ignore this email.

    best regards,
    POSTULAE
    """

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["to"] = to_email
    msg.set_content(body)

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        if EMAIL_USE_TLS:
            server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    
    except (SMTPException, SMTPAuthenticationError, ConnectionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        ) from exc