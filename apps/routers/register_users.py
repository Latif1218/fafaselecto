from fastapi import HTTPException, status, APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated
from ..models import users_model
from ..schemas import users_schema
from ..database import get_db
from ..utils import hashing


router = APIRouter(
    prefix="/register_user",
    tags=["Registration"]
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=users_schema.UserResponse)
def create_user(
    user: users_schema.UserCreate,
    db: Annotated[Session, Depends(get_db)]
):
    if db.query(users_model.User).filter(
        users_model.User.email == user.email
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = hashing.hash_password(user.password)
    user.password = hashed_password
    new_user = users_model.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user