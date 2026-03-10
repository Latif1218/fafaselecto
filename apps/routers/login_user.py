from fastapi import HTTPException, status, APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..database import get_db
from ..authentication import users_oauth
from ..models.users_model import User
from ..schemas import users_schema
from ..schemas.users_schema import UserResponse


router = APIRouter(
    prefix="",
    tags= ["Authentication or login"]
)


@router.post("/token", status_code=status.HTTP_200_OK, response_model=users_schema.UserToken)
def login_user_access_token(
    user_credentials : Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    """User login endpoint."""

    user = users_oauth.authenticate_user(db, user_credentials.username, user_credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Incorrect email or password. Please check and try again.",
            headers = {"WWW-Authenticate": "Bearer"}
        )
    
    access_token = users_oauth.create_access_token(
        data = {"user_id": user.id, "role": user.role},
        expires_delta=timedelta(minutes=users_oauth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "message": "Login successful. please allow location access.",
        "access_token": access_token,
        "token_type": "bearer"
    }



@router.get("/me", response_model = UserResponse ,status_code=status.HTTP_200_OK)
def user_schemas(
    current_user: Annotated[User, Depends(users_oauth.get_current_user)]
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Faild"
        )
    return current_user