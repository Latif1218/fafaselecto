import jwt
import requests
from jwt import ExpiredSignatureError, PyJWTError
from fastapi import Depends, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from ..schemas import users_schema
from ..models import users_model
from ..database import get_db
from ..utils.hashing import verify_password
from typing import Optional, Annotated
from datetime import datetime, timedelta, timezone
from ..config import JWT_SECRET_KEY
from uuid import UUID
from ..config import GOOGLE_USERINFO_URL

SECRET_KEY = JWT_SECRET_KEY
oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60



def get_user(db: Session, username: str):
    user = db.query(users_model.User).filter(
        users_model.User.email == username
    ).first()

    return user



def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = {}

    
    for key, value in data.items():
        if isinstance(value, UUID):
            to_encode[key] = str(value)
        else:
            to_encode[key] = value

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire.timestamp()})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def get_google_user_info(access_token: str):
    url = GOOGLE_USERINFO_URL
    headers = {"Authorization" : f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fatch Google user information."
        )
    
    return response.json()



def get_current_user(
    db: Annotated[ Session, Depends(get_db)],
    token: str = Depends(oauth2_schema)
) -> users_model.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("user_id")

        if user_id is None:
            raise credentials_exception from None
        
        token_data = users_schema.TokenData(id = user_id)

    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. please login again",
            headers={"WWW-Authenticate":"Bearer"}
        ) from e
    
    except PyJWTError as e:
        raise credentials_exception from e
    
    user = db.query(users_model.User).filter(
        users_model.User.id == token_data.id
    ).first()
    if user is None:
        raise credentials_exception from None
    
    return user




def get_current_active_user(
        current_user: Annotated[users_model.User, Depends(get_current_user)]
):
    if current_user.disabled: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user



def update_user(db: Session, user_id: int, update_data: dict):
    user = db.query(users_model.User).filter(
        users_model.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user



def get_current_admin_user(
        current_user: Annotated[users_model.User, Depends(get_current_user)]
)-> users_model.User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permission to access all user"
        )
    return current_user




def get_current_tutor_user(
        current_user: Annotated[users_model.User , Depends(get_current_user)]
) -> users_model.User:
    if current_user.role != users_model.UserRole.TUTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tutor access required"
        )
    return current_user