from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse
from datetime import timedelta
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.users_model import User, UserRole, UserPlan, UserStatus
from ..schemas.users_schema import UserResponse, UserToken, TokenData
from ..utils.hashing import hash_password
from ..utils.google_oauth_url import get_google_oauth_url
from ..authentication.users_oauth import create_access_token, get_google_user_info, ACCESS_TOKEN_EXPIRE_MINUTES
from ..config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, GOOGLE_TOKEN_URL
import secrets
import requests


router = APIRouter(
    prefix="/auth",
    tags=["Google Authentication"]
)


@router.get("/google/login")
async def google_login(request: Request):
    """Start Google OAuth authentication flow."""

    state = secrets.token_urlsafe(32)

    request.session["google_oauth_state"] = state

    auth_url = get_google_oauth_url(state)

    return RedirectResponse(auth_url)




@router.get("/google/callback", response_model=UserToken)
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """Google Oath callback endpoint."""

    session_state = request.session.get("google_oauth_state")

    if not session_state or session_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state"
        )
    
    token_payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    token_response = requests.post(GOOGLE_TOKEN_URL, data=token_payload)

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve Google access token"
        )
    
    token_data = token_response.json()

    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google access token not found"
        )
    

    google_user = get_google_user_info(access_token)

    email = google_user.get("email")
    name = google_user.get("name")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email not available"
        )
    
    user = db.query(User).filter(User.email == email).first()

    if not user:
        random_password = secrets.token_urlsafe(16)

        user = User(
            email = email,
            full_name = name,
            password = hash_password(random_password),
            role = UserRole.USER,
            plan = UserPlan.ESSENTIAL,
            status = UserStatus.ACTIVE
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    jwt_token = create_access_token(
        data={"user_id": user.id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": jwt_token,
        "token_type": "bearer"
    }